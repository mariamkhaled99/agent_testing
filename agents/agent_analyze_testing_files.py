import json
import uuid
import streamlit as st
import asyncio
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from models.module_method_model import CodeSnippetList
from utils import count_tokens, split_into_chunks, split_large_chunk
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import OpenAI
import os


load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_CHUNK_SIZE = 100000  # Define a safe chunk size to avoid token overflow
MAX_TOKENS = 16000  # Safe limit for gpt-3.5-turbo
RESERVED_PROMPT_TOKENS = 1000  # Reserve tokens for the prompt
client = OpenAI()

# Function to analyze repository content and identify languages/frameworks

import json
import uuid
import streamlit as st
import asyncio
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from models.module_method_model import CodeSnippetList
from utils import count_tokens, split_into_chunks, split_large_chunk
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import OpenAI
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_CHUNK_SIZE = 100000  # Define a safe chunk size to avoid token overflow
MAX_TOKENS = 16000  # Safe limit for gpt-3.5-turbo
RESERVED_PROMPT_TOKENS = 1000  # Reserve tokens for the prompt
client = OpenAI()

async def analyze_repo_content_need_testing(content: str,tree=None):
    safe_token_limit = MAX_TOKENS - RESERVED_PROMPT_TOKENS
    chunks = split_into_chunks(content, safe_token_limit)
    results = []

    for chunk in chunks:
        if count_tokens(chunk) > safe_token_limit:
            smaller_chunks = split_large_chunk(chunk, safe_token_limit)
        else:
            smaller_chunks = [chunk]

        for sub_chunk in smaller_chunks:
            if sub_chunk.strip():
                prompt_template = [
                    {"role": "system", "content": "You are a professional software engineer."},
                    {"role": "user", "content": f"""
                    Given this content of code: {sub_chunk.strip()} of this project, analyze the code to identify functions or classes that require testing.

                    Requirements:
                    - Identify only user-defined functions or classes explicitly defined in the provided code.
                    - Exclude any built-in functions, classes, or methods specific to Python, as well as any standard library elements or framework-provided constructs.
                    - List the identified functions or classes in a structured format.
                    - For each identified function or class:
                    - Provide a unique ID in the format "id": "<UUID>".
                    - Include the full path of the function or class in the code.
                    - Provide the name and type (e.g., "function" or "class").
                    - Include the complete code snippet defining the function or class.
                    - Library Used in test
                    - Purpose of this Unit test
                    - Do not return any explanation or comments along with the list.
                    

                    Return the result in the following JSON format:
                    {{
                        "snippets": [
                            {{
                                "id": "<UUID>",
                                "path": "path for function_or_class",
                                "name": "function_or_class",
                                "type": "type_code",
                                "code": "full_code_snippet"
                            }},
                            ...
                        ]
                    }}
                    """}
                ]

                try:
                   

                    ai=client.beta.chat.completions.parse( model="gpt-4o-mini-2024-07-18",messages=prompt_template, response_format=CodeSnippetList)
                    parsed_results = ai.choices[0].message.parsed

                    print("==============================================================================================")
                    print(f"parsed_results using parser: {parsed_results}")

                    # for snippet in parsed_results.snippets:
                    #     snippet.id = uuid.uuid4()

                    # Append the parsed results to the final results list
                    # results = parsed_results.snippets
                    parsed_results = [
                                {
                                    "id":str(uuid.uuid4()),
                                    "path": snippet.path,
                                    "name": snippet.name,
                                    "type": snippet.type,
                                    "code": snippet.code
                                }
                                for snippet in parsed_results.snippets
                            ]
                    json_output = json.dumps(parsed_results, indent=4)
                    print(f"json_output:{json_output}")
                    return json_output

       


                except Exception as e:
                    print(f"Error during OpenAI API call files: {str(e)}")
                    results.append(f"Error processing this sub-chunk: {str(e)}")
    
    # flat_results = [item for sublist in results for item in sublist if isinstance(sublist, list)]
    # return flat_results