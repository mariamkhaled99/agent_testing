import json
import uuid
import streamlit as st
import asyncio
from langchain.prompts import PromptTemplate
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

# Function to analyze repository content and identify languages/frameworks

async def analyze_repo_content_need_testing(content: str):
    # Define safe token limit for content chunks
    safe_token_limit = MAX_TOKENS - RESERVED_PROMPT_TOKENS
    
    # Split content into manageable chunks
    chunks = split_into_chunks(content, safe_token_limit)
    results = []

    for chunk in chunks:
        # Further split if a chunk exceeds the safe token limit
        if count_tokens(chunk) > safe_token_limit:
            smaller_chunks = split_large_chunk(chunk, safe_token_limit)
        else:
            smaller_chunks = [chunk]

        for sub_chunk in smaller_chunks:
            if sub_chunk.strip():  # Skip empty chunks
                prompt_template = f"""
                Given this content of code: {sub_chunk.strip()} of this project, analyze the code to identify functions or classes that require testing.

                Requirements:
                - Identify only user-defined functions or classes explicitly defined in the provided code.
                - Exclude any built-in functions, classes, or methods specific to the python , as well as any standard library elements or framework-provided constructs.
                - List the identified functions or classes in a structured format.
                - For each identified function or class:
                - Provide a unique ID in the format "id": "<UUID>".
                - Include the full path of the function or class in the code.
                - Provide the name and type (e.g., "function" or "class").
                - Include the complete code snippet defining the function or class.
                - Library Used in test
                - Purpose of this Unit test
                - Do not return any explanation or comments along with the list.


                Return the result in the following format:
                [
                    {{  "id": "<UUID>",
                        "path": "path for function_or_class",
                        "name": "function_or_class",
                        "type": "type_code",
                        "code": "full_code_snippet"
                    }},
                    ...
                ]
                """

                message = HumanMessage(content=prompt_template)
                
                try:
                    # Initialize OpenAI API client with error handling
                    ai = ChatOpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY, temperature=0)
                    ai_response = await ai.ainvoke([message])

                    # Parse the response, and if possible, append unique UUIDs for entries
                    response_content = ai_response.content.strip()
                    print(f"response_content: {response_content}")
                    safe_response_content = json.dumps(json.loads(response_content))
                    parsed_results = json.loads(safe_response_content)
                   
                    print("==============================================================================================")
                    print(f"parsed_results: {parsed_results}")
                    
                    # Add unique UUID to each entry
                    for item in parsed_results:
                        item["id"] = str(uuid.uuid4())

                    results.append(parsed_results)

                except Exception as e:
                    print(f"Error during OpenAI API call files: {str(e)}")
                    results.append(f"Error processing this sub-chunk: {str(e)}")
    
    # Combine all results into a single list of JSON entries
    flat_results = [item for sublist in results for item in sublist if isinstance(sublist, list)]
    return flat_results