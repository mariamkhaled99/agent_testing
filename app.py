import streamlit as st
import asyncio
from gitingest import ingest
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Use an event loop policy compatible with subprocesses on Windows
if hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Title of the app
st.title("Git Repository Analysis Agent")

# Input field for GitHub repository URL
repo_url = st.text_input("Enter the GitHub Repository URL:", placeholder="https://github.com/user/repo")
print(f"repo_url: {repo_url}")
OPENAI_API_KEY=''
import re

async def analyze_repo_content(content: str):
    # Split content based on the "File: /path/to/file" pattern to avoid token overflow
    chunks = re.split(r'(\n={60,}\nFile: [^\n]+)', content)
    
    results = []
    for chunk in chunks:
        if chunk.strip():  # Skip empty chunks
            prompt_template = f"""
            Given the content of code: {chunk.strip()} of this project, analyze the code to identify the major programming languages and frameworks used in this project. Follow these steps to make your analysis:

            1. **File Extensions**: Look at the file extensions in the project. Common extensions include:
               - `.py` for Python
               - `.js` for JavaScript
               - `.java` for Java
               - `.rb` for Ruby
               - `.php` for PHP
               - `.html`, `.css`, `.scss` for web technologies
               - `.ts` for TypeScript
               - `.cpp`, `.h` for C++
               - `.cs` for C#

            2. **Configuration Files**: Check for configuration files that specify dependencies or frameworks. Common files include:
               - `package.json` for Node.js projects (JavaScript frameworks like React, Angular, or Vue.js).
               - `requirements.txt` or `Pipfile` for Python projects (frameworks like Django, Flask).
               - `Gemfile` for Ruby projects (frameworks like Rails).
               - `pom.xml` or `build.gradle` for Java projects (frameworks like Spring).
               - `composer.json` for PHP projects (frameworks like Laravel, Symfony).
               - `Dockerfile` or `docker-compose.yml` which might provide hints about the technology stack.

            3. **Framework-Specific Files**: Some frameworks have specific files or directories:
               - `app/` and `config/` for Ruby on Rails projects.
               - `src/` and `public/` for React, Angular, or similar frameworks.
               - `manage.py` or `app.py` for Django or Flask.

            4. **Documentation and Comments**: Sometimes, documentation files like `README.md` or inline comments in the code indicate the frameworks and languages used. Look for any mention of the tech stack in these files.

            Your task is to identify the **programming languages** (such as Python, JavaScript, Ruby, etc.) and **frameworks** (such as Django, React, Angular, Rails, etc.) used in the project. Provide a list of the major languages and frameworks found in the repository.

            Be sure to mention the specific language and framework for each section based on the observations from the code and configuration files.
            """
            message = HumanMessage(content=prompt_template)
            
            try:
                # Initialize OpenAI API client with error handling
                ai = ChatOpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY, temperature=0)
                ai_response = await ai.ainvoke([message])
                results.append(ai_response.content.strip())
            
            except Exception as e:
                print(f"Error during OpenAI API call: {str(e)}")
                results.append(f"Error processing this chunk: {str(e)}")
    
    return "\n".join(results)

    
# Function to analyze repository content and identify languages/frameworks

async def analyze_repo_content_need_testing(content: str):
    # Split content based on the "File: /path/to/file" pattern to avoid token overflow
    chunks = re.split(r'(\n={60,}\nFile: [^\n]+)', content)
    
    results = []
    for chunk in chunks:
        if chunk.strip():  # Skip empty chunks
            prompt_template = f"""
            Given this content of code: {chunk.strip()} of this project, analyze the code to identify functions, classes, and modules that require testing.
            Make sure to list them.
            """
            message = HumanMessage(content=prompt_template)
            
            try:
                # Initialize OpenAI API client with error handling
                ai = ChatOpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY, temperature=0)
                ai_response = await ai.ainvoke([message])
                results.append(ai_response.content.strip())
            
            except Exception as e:
                print(f"Error during OpenAI API call: {str(e)}")
                results.append(f"Error processing this chunk: {str(e)}")
    
    return "\n".join(results)



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
