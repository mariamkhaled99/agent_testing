import streamlit as st
import asyncio
from gitingest import ingest

from dotenv import load_dotenv
import os

from agent_analyze_langs import analyze_repo_content
from agent_analyze_testing_files import analyze_repo_content_need_testing


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
            # print(f"tree: {tree}")
            # print(f"content: {content}")

            # Display summary, tree, and content as plain text
            st.subheader("Repository Summary")
            with st.container():
                st.markdown(f"<div class='scrollable-section'>{str(summary)}</div>", unsafe_allow_html=True)

            # Perform analysis on the content when the button is clicked
            
            analysis_result = asyncio.run(analyze_repo_content(content))
            st.subheader("Frameworks and Languages Used")
            st.text(analysis_result)
            print(f"analysis_result:{analysis_result}")
            st.text(analysis_result)
            analysis_result = asyncio.run(analyze_repo_content_need_testing(content))
            st.subheader("Classes And Modules need to be tested")
            print(f"analysis_result:{analysis_result}")
            st.text(analysis_result)

        except Exception as e:
            st.error(f"An error occurred: {e}")
            import traceback
            st.text(traceback.format_exc())
    else:
        st.warning("Please enter a valid repository URL.")
