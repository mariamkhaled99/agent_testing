import streamlit as st
import asyncio
import json
from gitingest import ingest
from dotenv import load_dotenv
import os
from agent_analyze_langs import analyze_repo_content
from agent_analyze_testing_files import analyze_repo_content_need_testing
from agent_generate_test_suite import generate_unit_testing


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
            
            modules_need_testing_json=json.dumps(analysis_result_testing, indent=4)
            print('==============================================================================================')
            print(f"modules_need_testing: {modules_need_testing_json}")
            print('==============================================================================================')
            analysis_result_langs_json=json.dumps(analysis_result_langs, indent=4)
            print(f"analysis_result_langs: {analysis_result_langs_json}")
            print('==============================================================================================')
            
            unit_test_result= asyncio.run(generate_unit_testing(modules_need_testing_json,analysis_result_langs_json))
            # Create a dictionary with the results
            result_data = {
                "repo_url": repo_url,
                "summary": summary,
                "frameworks_and_languages":analysis_result_langs,
                "modules_need_testing": analysis_result_testing,
                "unit_test_result": unit_test_result
            }

            # Convert dictionary to JSON string
            result_json = json.dumps(result_data, indent=4)
            
            # Display the JSON data
            st.subheader("Analysis Results in JSON Format")
            st.json(result_data)  # Display the JSON in a formatted way

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
