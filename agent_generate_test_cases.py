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


async def generate_test_cases(modules_need_testing_json: str, languages_json: str):
    """
    Generates unit tests based on the provided modules and the language information.
    
    Parameters:
    - modules_need_testing_json (str): JSON containing the modules or code needing testing.
    - languages_json (str): JSON containing information about the languages used in the code.

    Returns:
    - List of dictionaries containing unit test code, filenames, and unique IDs.
    """
    
    # Define safe token limit for content chunks
    safe_token_limit = MAX_TOKENS - RESERVED_PROMPT_TOKENS

    # Parse modules and languages from the provided JSONs
    try:
        modules = json.loads(modules_need_testing_json)
    except json.JSONDecodeError as e:
        print(f"Error parsing modules_need_testing_json: {e}")
        return []

    # Try to parse the languages JSON safely
    try:
        languages = json.loads(languages_json)
    except json.JSONDecodeError as e:
        print(f"Error parsing languages_json: {e}")
        return []

    # Ensure that languages_json is a list and the first item has the expected structure
    # or len(languages) == 0 or not isinstance(languages[0], dict) or "languages" not in languages[0]
    if not isinstance(languages, dict) or len(languages.get('languages')) == 0 or not isinstance(languages.get('languages')[0], str):
        print("Invalid format for languages_json. It should be a list of dictionaries with a 'languages' key.")
        return []

    # Split the modules into chunks and prepare the results container
    results = []

    # Loop through the modules and process each one
    for module in modules:
        # Split the content of each module into manageable chunks
        chunks = split_into_chunks(module['code'], safe_token_limit)

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

                    prompt_template = f"""
                        Given the following code written in {language_used}:
                        
                        {sub_chunk.strip()}
                        
                        Analyze the provided code and perform the following tasks:
                        1. Identify all functions and classes in the code that require unit testing.
                        2. For each identified function or class:
                            - Generate possible test cases, including:
                                - **Positive Test Cases**: Test cases that validate the expected behavior under normal conditions.
                                - **Negative Test Cases**: Test cases that validate the behavior under invalid or edge conditions.
                                - **Boundary Test Cases**: Test cases that validate the behavior at the boundaries of input domains.
                                - **Error Handling Test Cases**: Test cases that validate the behavior when errors or exceptions are expected.
                            - Provide detailed information for each test case, including:
                                - **Test Case ID**: A unique identifier for the test case.
                                - **Test Name**: A brief and descriptive name for the test case (e.g., "test_add_positive_numbers", "test_divide_by_zero").
                                - **Description**: A detailed explanation of the test case purpose.
                                - **Test Data**: Input data for the test case.
                                - **function_id**: A unique identifier for the function or class being tested .
                                - **Expected Output**: The expected outcome of the test case.
                            - Ensure that the generated test cases cover various scenarios and edge cases.
                        Do not return any explanation or comments along with the list.
                        Return the result in the following JSON format:
                        [
                            {{
                                "function": "<function_name>",
                                "function_id": "<UUID_for_function>",
                                "test_cases": [
                                    {{
                                        "test_case_id": "<UUID_for_test_case>",
                                        "test_name": "<test_name>",
                                        "description": "<description>",
                                        "test_data": <test_data>,
                                        "expected_output": <expected_output>
                                    }},
                                    ...
                                ]
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
                        parsed_results = json.loads(response_content)  # Assuming OpenAI provides valid JSON-like data
                        
                        # Add unique UUIDs to each entry
                        for item in parsed_results:
                        #    item["function_id"] = str(uuid.uuid4())  # UUID for unit test
                           item["test_case_id"] = str(uuid.uuid4())  # UUID for the test file

                        results.append(parsed_results)

                    except Exception as e:
                        print(f"Error during OpenAI API call unit test cases: {str(e)}")
                        results.append(f"Error processing this chunk: {str(e)}")

    # Combine all results into a single list of JSON entries
    flat_results = [item for sublist in results for item in sublist if isinstance(sublist, list)]
    return flat_results
