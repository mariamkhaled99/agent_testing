import asyncio
import base64
from flask import Flask, json, request, jsonify
import threading
import requests
import streamlit as st
from gitingest import ingest
from dotenv import load_dotenv
import os
from add_test_interperator import run_test
from agents.agent_analyze_langs import analyze_repo_content
from agents.agent_analyze_testing_files import analyze_repo_content_need_testing
from agents.agent_generate_test_cases import generate_test_cases
from agents.agent_generate_test_code import generate_unit_testing_code
import pdfplumber
from langchain_community.chat_message_histories import (
    StreamlitChatMessageHistory,
)

from github_app_auth import generate_jwt, get_installation_access_token
from utils import get_repo_name

load_dotenv()

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# GITHUB_APP_ID= os.getenv("GITHUB_APP_ID")
# GITHUB_APP_PRIVATE_KEY_FILE=os.getenv("GITHUB_APP_PRIVATE_KEY_File")
# # GITHUB_APP_PRIVATE_KEY=os.getenv("GITHUB_APP_PRIVATE_KEY")

# # GITHUB_REPOSITORY=os.getenv("GITHUB_REPOSITORY")

# # # Read the private key from the file
# if GITHUB_APP_PRIVATE_KEY_FILE:
#     with open(GITHUB_APP_PRIVATE_KEY_FILE, "r") as key_file:
#         GITHUB_APP_PRIVATE_KEY = key_file.read()

GITHUB_APP_ID= os.getenv("GITHUB_APP_ID")
GITHUB_APP_PRIVATE_KEY_FILE=os.getenv("GITHUB_APP_PRIVATE_KEY")
GITHUB_REPOSITORY=os.getenv("GITHUB_REPOSITORY")

# Read the private key from the file
if GITHUB_APP_PRIVATE_KEY_FILE:
    with open(GITHUB_APP_PRIVATE_KEY_FILE, "r") as key_file:
        GITHUB_APP_PRIVATE_KEY = key_file.read()


# Generate JWT
jwt_token = generate_jwt(GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY)

# Get installation access token
access_token = get_installation_access_token(jwt_token, GITHUB_REPOSITORY)


# Use an event loop policy compatible with subprocesses on Windows
if hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


# Initialize Flask app for webhook handling
app = Flask(__name__)

def handle_webhook_delivery(payload, event_type):
    """
    Handles GitHub webhook deliveries for push and pull_request events.
    """
    
    # print(f"payload: {payload}")
    print("===========================================================================================")
    # 'contents_url': 'https://api.github.com/repos/mariamkhaled99/ABI-Backend-Assesment/contents/{+path}'
    # Get the contents_url template
    content_url = payload.get('repository', {}).get('contents_url')

    # Initialize lists to store added, removed, and modified files
    added_files = []
    removed_files = []
    modified_files = []

    # Extract added, removed, and modified files from the commits
    commits = payload.get('commits', [])
    for commit in commits:
        added_files.extend(commit.get('added', []))
        removed_files.extend(commit.get('removed', []))
        modified_files.extend(commit.get('modified', []))


    # Combine all paths into a dictionary
    paths = {
        'added': added_files,
        'removed': removed_files,
        'modified': modified_files
    }
    
    print(f"content_url: {content_url}")   
    print("===========================================================================================")
 
    print(f"paths: {paths}")
    repository = payload.get('repository', {}).get('full_name')
    repo_url = f"https://github.com/{repository}"

    # if repository != "mariamkhaled99/ABI-Backend-Assesment":  # Replace with your repo name
    #     print(f"Ignoring event for repository: {repository}")
    #     return
    if event_type == 'push':
        analysis_result_testing = []
        test_cases = []
        test_code=[]

        # Handle push event
        branch = payload.get('ref').split('/')[-1]  # Extract branch name
        commits = payload.get('commits', [])
        print(f"Push event received for branch: {branch}")
        print(f"Number of commits: {len(commits)}")

        # Loop over each category (added, removed, modified)
        for category, file_paths in paths.items():
            if file_paths:  # Check if the list is not empty
                print(f"Processing {category} files:")
                for file_path in file_paths:
                    # Replace {+path} in the contents_url with the file path
                    content_url = content_url.replace('{+path}', file_path)
                    print(f"Fetching content from: {content_url}")

                    # Make a GET request to fetch the file content
                    response = requests.get(content_url)
                    if response.status_code == 200:
                        file_data = response.json()
                        file_name = file_data.get('name')
                        file_content_encoded = file_data.get('content')
                        file_content_decoded = base64.b64decode(file_content_encoded).decode('utf-8')

                        print(f"File: {file_name}")
                        print("===========================================================================================")
                        print(f"Decoded Content:\n{file_content_decoded}")
                        content = file_content_decoded

                        # Perform analysis on the content
                        try:
                            analysis_result_langs = asyncio.run(analyze_repo_content(content))
                            analysis_result_testing_json = asyncio.run(analyze_repo_content_need_testing(content))
                            print('==============================================================================================')
                            print(f"analysis_result_langs before json: {analysis_result_langs}")
                            print('==============================================================================================')
                            print('==============================================================================================')
                            print(f"modules_need_testing: {analysis_result_testing_json}")
                            print('==============================================================================================')
                            analysis_result_langs_json = json.dumps(analysis_result_langs, indent=4)
                            print(f"analysis_result_langs: {analysis_result_langs_json}")
                            print('==============================================================================================')

                            test_cases_json = asyncio.run(generate_test_cases(analysis_result_testing_json, analysis_result_langs_json, "", True))
                            test_code_json=asyncio.run(generate_unit_testing_code(test_cases_json,analysis_result_langs_json,True))
                            print(f"unit tests:{test_code_json}")
                            print('==============================================================================================')
                            
                            


                        except Exception as e:
                            print(f"An error occurred during analysis: {e}")
                            continue

        # Create a dictionary with the results
        result_data = {
            "repo_url": repo_url,
            "frameworks_and_languages": analysis_result_langs,
            "modules_need_testing": analysis_result_testing_json,
            "test_cases": test_cases_json,
            "unit_tests":test_code_json
        }

        print(f"result_data: {result_data}")
        
        # Convert dictionary to JSON string
        result_json = json.dumps(result_data, indent=4)
        user_repo = repo_url.replace("https://github.com/", "")
        # Remove any trailing slashes or additional paths
        user_repo = user_repo.split("/")[0] + "/" + user_repo.split("/")[1]
        print(f"Extracted user/repo: {user_repo}")
        
        repo_fullname=user_repo
        history = StreamlitChatMessageHistory(key=f"{repo_fullname}")

        history.add_user_message(result_json )
        print("==========================================================================================")
        print(f"history.messages:{history.messages}")
        print("===========================================================================================")
        # Display the JSON data
        st.subheader("Analysis Results in JSON Format")
        st.json(result_data)  # Display the JSON in a formatted way
        
        languages= analysis_result_langs.get('languages')
        
        print(f"analysis_result_langs:{analysis_result_langs}")
        
        repo_name=repo_name = get_repo_name(repo_url)
        
        run_test(repo_url,repo_name,test_code,languages)

        # You can also save it to a file if needed
        with open("repo_analysis_result.json", "w") as json_file:
            json.dump(result_data, json_file, indent=4)
        st.success("Results saved to repo_analysis_result.json")


    # elif event_type == 'pull_request':
    #     # Handle pull_request event (includes merge actions)
    #     action = payload.get('action')
    #     pr_number = payload.get('number')
    #     pr_title = payload.get('pull_request', {}).get('title')
    #     merged = payload.get('pull_request', {}).get('merged')

    #     if action == 'closed' and merged:
    #         print(f"Pull request #{pr_number} was merged: {pr_title}")
    #     elif action == 'closed' and not merged:
    #         print(f"Pull request #{pr_number} was closed without merging: {pr_title}")
    #     else:
    #         print(f"Unhandled action for pull_request event: {action}")

    # else:
    #     print(f"Ignoring unhandled event type: {event_type}")

# Register the /webhook route
@app.route('/webhook', methods=['POST'])
def webhook():
    # Respond to indicate that the delivery was successfully received
    response = jsonify({'status': 'Accepted'})
    response.status_code = 202

    # Check the `x-github-event` header to learn what event type was sent
    github_event = request.headers.get('X-GitHub-Event')

    # Handle the webhook delivery
    handle_webhook_delivery(request.json, github_event)

    return response

def run_webhook_server():
    """Run the Flask webhook server on port 3000."""
    app.run(host='0.0.0.0', port=3001)  # Listen on all network interfaces

# Start the webhook server in a separate thread
webhook_thread = threading.Thread(target=run_webhook_server)
webhook_thread.daemon = True  # Daemonize thread to stop it when the main program exits
webhook_thread.start()


# Title of the app
st.title("Git Repository Analysis Agent")

# Input field for GitHub repository URL
repo_url = st.text_input("Enter the GitHub Repository URL:", placeholder="https://github.com/user/repo")
print(f"repo_url: {repo_url}")

# Streamlit App
st.title("GitHub Webhook Listener with Streamlit")
st.write("This Streamlit app listens for GitHub webhooks in the background.")

# Add your Streamlit components here
st.write("Check the console for webhook events.")


    
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
            user_repo = repo_url.replace("https://github.com/", "")
            # Remove any trailing slashes or additional paths
            user_repo = user_repo.split("/")[0] + "/" + user_repo.split("/")[1]
            print(f"Extracted user/repo: {user_repo}")
           
            repo_fullname=user_repo
            history = StreamlitChatMessageHistory(key=f"{repo_fullname}")

            history.add_user_message(result_json )
            print("==========================================================================================")
            print(f"history.messages:{history.messages}")
            print("===========================================================================================")
            # Display the JSON data
            st.subheader("Analysis Results in JSON Format")
            st.json(result_data)  # Display the JSON in a formatted way
            
            languages= analysis_result_langs.get('languages')
            
            print(f"analysis_result_langs:{analysis_result_langs}")
            
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
