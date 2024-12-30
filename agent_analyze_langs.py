import streamlit as st
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from utils import count_tokens, split_into_chunks, split_large_chunk
from dotenv import load_dotenv
import os


load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_CHUNK_SIZE = 100000  # Define a safe chunk size to avoid token overflow
MAX_TOKENS = 16000  # Safe limit for gpt-3.5-turbo
RESERVED_PROMPT_TOKENS = 1000  # Reserve tokens for the prompt


async def analyze_repo_content(content: str):
    # Split content based on the "File: /path/to/file" pattern to avoid token overflow
    
    
    safe_token_limit = MAX_TOKENS - RESERVED_PROMPT_TOKENS
    chunks = split_into_chunks(content, safe_token_limit)
    results = []

    for chunk in chunks:
        # If chunk is still too large, split further based on token count
        if count_tokens(chunk) > safe_token_limit:
            smaller_chunks = split_large_chunk(chunk, safe_token_limit)
        else:
            smaller_chunks = [chunk]

        for sub_chunk in smaller_chunks:
            if sub_chunk.strip():  # Skip empty chunks
                prompt_template = f"""
                Given the content of code: {sub_chunk.strip()} of this project, analyze the code to identify the major programming languages and frameworks used in this project. Follow these steps to make your analysis:

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
                    results.append(f"Error processing this sub-chunk: {str(e)}")
    
    return "\n".join(results)
