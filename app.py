import streamlit as st
import asyncio
import json
from gitingest import ingest
from dotenv import load_dotenv
import os
from add_test_interperator import run_test
from agents.agent_analyze_langs import analyze_repo_content
from agents.agent_analyze_testing_files import analyze_repo_content_need_testing
from agents.agent_generate_test_cases import generate_test_cases
from agents.agent_generate_test_code import generate_unit_testing_code
import pdfplumber
from github_app_auth import generate_jwt, get_installation_access_token
from utils import get_repo_name

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Use an event loop policy compatible with subprocesses on Windows
if hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


# Title of the app
st.title("Git Repository Analysis Agent")

# Input field for GitHub repository URL
repo_url = st.text_input("Enter the GitHub Repository URL:", placeholder="https://github.com/user/repo")
print(f"repo_url: {repo_url}")


# GITHUB_APP_ID= os.getenv("GITHUB_APP_ID")
# GITHUB_APP_PRIVATE_KEY_FILE=os.getenv("GITHUB_APP_PRIVATE_KEY")
# GITHUB_REPOSITORY=os.getenv("GITHUB_REPOSITORY")

# # Read the private key from the file
# if GITHUB_APP_PRIVATE_KEY_FILE:
#     with open(GITHUB_APP_PRIVATE_KEY_FILE, "r") as key_file:
#         GITHUB_APP_PRIVATE_KEY = key_file.read()


# # Generate JWT
# jwt_token = generate_jwt(GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY)

# # Get installation access token
# access_token = get_installation_access_token(jwt_token, GITHUB_REPOSITORY)

# # Define a GraphQL query
# query = """


# query {
#   repository(owner: "mariamkhaled99", name: "ABI-Backend-Assesment") {
#     defaultBranchRef {
#       target {
#         ... on Commit {
#           oid
#           history(first: 1) {
#             edges {
#               node {
                
#                 message
#                 committedDate
#                 changedFilesIfAvailable
             
#                 }
#               }
#             }
#           }
#         }
#       }
#     }
#   }

#   # repository(owner: "mariamkhaled99", name: "ABI-Backend-Assesment") {
#   #   ref(qualifiedName: "main") {
#   #     target {
#   #       commitUrl
#   #     }
#   #   }
#   # }
  


# """

# # Replace OWNER and REPO with your repository details
# query = query.replace("OWNER", GITHUB_REPOSITORY.split("/")[0])
# query = query.replace("REPO", GITHUB_REPOSITORY.split("/")[1])

# # Make the GraphQL request
# result = make_graphql_request(access_token, query)
# print(result)




    
    
st.title("PDF Upload and Processing in Streamlit")

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

if uploaded_file:
    try:
        # Extract text from the uploaded PDF
        with pdfplumber.open(uploaded_file) as pdf:
            extracted_text = ""
            for page in pdf.pages:
                extracted_text += page.extract_text() + "\n"

        # Print the extracted text in the terminal
        print("Extracted Text from PDF:")
        print(extracted_text)
        st.subheader("Extracted Text from PDF")
        st.text_area("PDF Content:", extracted_text, height=300)

    except Exception as e:
        print(f"Error processing PDF: {e}")

# Define custom CSS for scrollable sections
st.markdown(
    """
    <style>
    .scrollable-section {
        max-height: 300px;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 5px;
        background-color: #f9f9f9;
        color: #000; 
        font-family: monospace;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if st.button("Analyze Repository"):
    if repo_url:
        try:
            # Ensure repo_url is valid before proceeding
            if not repo_url.startswith("http"):
                raise ValueError("The provided URL must start with 'http' or 'https'.")

            st.info("Processing the repository, please wait...")
            print("before ingest")
            summary, tree, content = ingest(repo_url)  # Ensure repo_url is defined here
            print(f"summary: {summary}")

            # Perform analysis on the content
            analysis_result_langs = asyncio.run(analyze_repo_content(content))
            analysis_result_testing = asyncio.run(analyze_repo_content_need_testing(content))
            print('==============================================================================================')
            print(f"analysis_result_langs before json: {analysis_result_langs}")
            print('==============================================================================================')
            print('==============================================================================================')
            
            # modules_need_testing_json=json.dumps(analysis_result_testing, indent=4)
            print('==============================================================================================')
            print(f"modules_need_testing: {analysis_result_testing}")
            print('==============================================================================================')
            analysis_result_langs_json=json.dumps(analysis_result_langs, indent=4)
            print(f"analysis_result_langs: {analysis_result_langs_json}")
            print('==============================================================================================')


            test_cases= asyncio.run(generate_test_cases(analysis_result_testing,analysis_result_langs_json,extracted_text,False))
            # test_cases_json=json.dumps(test_cases, indent=4)
            test_code=asyncio.run(generate_unit_testing_code(test_cases,analysis_result_langs_json,False))
            # Create a dictionary with the results
            result_data = {
                "repo_url": repo_url,
                "summary": summary,
                "frameworks_and_languages":analysis_result_langs,
                "modules_need_testing": analysis_result_testing,
                "test_cases": test_cases,
                "test_code":test_code
            }

            # Convert dictionary to JSON string
            result_json = json.dumps(result_data, indent=4)
            
            languages= analysis_result_langs.get('languages')
            
            print(f"analysis_result_langs:{analysis_result_langs}")
           
            
            
            
            # Display the JSON data
            st.subheader("Analysis Results in JSON Format")
            st.json(result_data)  # Display the JSON in a formatted way
            
            repo_name=repo_name = get_repo_name(repo_url)
            
            run_test(repo_url,repo_name,test_code,languages)

            # You can also save it to a file if needed
            with open("repo_analysis_result.json", "w") as json_file:
                json.dump(result_data, json_file, indent=4)
            st.success("Results saved to repo_analysis_result.json")

        except Exception as e:
            st.error(f"An error occurred: {e}")
            import traceback
            st.text(traceback.format_exc())
    else:
        st.warning("Please enter a valid repository URL.")
