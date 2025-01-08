import streamlit as st
import asyncio
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from utils import count_tokens, split_into_chunks, split_large_chunk
from dotenv import load_dotenv
import os
import uuid
import json

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_CHUNK_SIZE = 100000  # Define a safe chunk size to avoid token overflow
MAX_TOKENS = 16000  # Safe limit for gpt-3.5-turbo
RESERVED_PROMPT_TOKENS = 1000  # Reserve tokens for the prompt

# Function to analyze repository content and identify languages/frameworks

async def generate_unit_testing_code(test_cases_json: str, languages_json: str):
    """
    Generates unit tests based on the provided test cases and the language information.
    
    Parameters:
    - test_cases_json (str): JSON containing the test cases for the functions.
    - languages_json (str): JSON containing information about the languages used in the code.

    Returns:
    - List of dictionaries containing unit test code, filenames, and unique IDs.
    """
    
    # Define safe token limit for content chunks
    safe_token_limit = MAX_TOKENS - RESERVED_PROMPT_TOKENS

    # Parse test cases and languages from the provided JSONs
    try:
        test_cases = json.loads(test_cases_json)
    except json.JSONDecodeError as e:
        print(f"Error parsing test_cases_json: {e}")
        return []

    try:
        languages = json.loads(languages_json)
    except json.JSONDecodeError as e:
        print(f"Error parsing languages_json: {e}")
        return []

    # Validate the structure of languages_json
    if not isinstance(languages, dict) or len(languages.get('languages')) == 0 or not isinstance(languages.get('languages')[0], str):
        print("Invalid format for languages_json. It should be a dictionary with a 'languages' key containing a list of strings.")
        return []

    # Prepare the results container
    results = []

    # Loop through the test cases and process each one
    for test_case in test_cases:
        function_name = test_case.get("function", "Unknown")
        function_id = test_case.get("function_id", str(uuid.uuid4()))
        test_cases_list = test_case.get("test_cases", [])

        # Convert the test cases list to a JSON string for chunking
        test_cases_json_str = json.dumps(test_cases_list, indent=2)

        # Split the test cases JSON into manageable chunks
        chunks = split_into_chunks(test_cases_json_str, safe_token_limit)

        for chunk in chunks:
            # Further split if a chunk exceeds the safe token limit
            if count_tokens(chunk) > safe_token_limit:
                smaller_chunks = split_large_chunk(chunk, safe_token_limit)
            else:
                smaller_chunks = [chunk]

            for sub_chunk in smaller_chunks:
                if sub_chunk.strip():  # Skip empty chunks
                    # Get the language used (assuming you want the first language)
                    language_used = " ".join(languages["languages"]) if languages else "Unknown"

                    # Prepare the prompt for generating unit tests
                    prompt_template = f"""
                    Given the following function in {language_used}:

                    Function Name: {function_name}
                    Function ID: {function_id}

                    Test Cases:
                    {sub_chunk.strip()}

                    Requirements:
                    - Generate unit tests for the function based on the provided test cases.
                    - Use the appropriate testing framework for {language_used} (e.g., unittest for Python).
                    - Ensure the unit tests cover all provided test cases, including their descriptions and expected outputs.
                    - Include assertions to validate the expected outputs.
                    - Provide the name of the test file and its unique ID.
                    -provide the name of the test library used in the test.
                    - Ensure the code is complete and ready to be used for unit testing.
                    - Do not include any irrelevant code.
                    - Do not return any explanation or comments along with the list.

                    Return only the result in the following format:
                    [
                        {{
                            "unit_test_code": "<unit_test_code>",
                            "test_library": "<test_library>",
                            "name_unit_test_file": "<name_of_test_file>",
                            "unit_test_id": "<UUID_for_unit_test>",
                            "id": "<UUID_for_test_code_file>"
                        }},
                        ...
                    ]
                    """

                    message = HumanMessage(content=prompt_template)
                    
                    try:
                        # Initialize OpenAI API client with error handling
                        ai = ChatOpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY, temperature=0)
                        ai_response = await ai.ainvoke([message])

                        # Parse the response and append unique UUIDs for entries
                        response_content = ai_response.content.strip()
                        print(f"response_content for code : {response_content}")
                        parsed_results = json.loads(response_content)  # Assuming OpenAI provides valid JSON-like data
                        
                        # Add unique UUIDs to each entry
                        for item in parsed_results:
                            item["unit_test_id"] = str(uuid.uuid4())  # UUID for unit test
                            item["id"] = str(uuid.uuid4())  # UUID for the test file

                        results.append(parsed_results)

                    except Exception as e:
                        print(f"Error during OpenAI API call unit test code: {str(e)}")
                        results.append(f"Error processing this chunk: {str(e)}")

    # Combine all results into a single list of JSON entries
    flat_results = [item for sublist in results for item in sublist if isinstance(sublist, list)]
    return flat_results