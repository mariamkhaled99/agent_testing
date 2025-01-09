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

async def generate_test_cases(modules_need_testing_json: str, languages_json: str, extracted_text: str):
    """
    Generates unit tests based on the provided modules, the language information, and the extracted text.
    
    Parameters:
    - modules_need_testing_json (str): JSON containing the modules or code needing testing.
    - languages_json (str): JSON containing information about the languages used in the code.
    - extracted_text (str): The extracted text containing requirements for UAT.

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

    try:
        languages = json.loads(languages_json)
    except json.JSONDecodeError as e:
        print(f"Error parsing languages_json: {e}")
        return []

    if not isinstance(languages, dict) or len(languages.get('languages')) == 0 or not isinstance(languages.get('languages')[0], str):
        print("Invalid format for languages_json. It should be a list of dictionaries with a 'languages' key.")
        return []

    # Split the extracted text into chunks
    extracted_text_chunks = split_into_chunks(extracted_text, safe_token_limit)
    print("========================================text chunks=============================================")
    print(f"extracted_text_chunks: {extracted_text_chunks}")
    results = []

    for module in modules:
        chunks = split_into_chunks(module['code'], safe_token_limit)

        for chunk in chunks:
            if count_tokens(chunk) > safe_token_limit:
                smaller_chunks = split_large_chunk(chunk, safe_token_limit)
            else:
                smaller_chunks = [chunk]

            for sub_chunk in smaller_chunks:
                if sub_chunk.strip():
                    language_used = " ".join(languages["languages"]) if languages else "Unknown"

                    for text_chunk in extracted_text_chunks:
                        prompt_template = f"""
                        Given the following code written in {language_used}:

                        {sub_chunk.strip()}

                        Analyze the provided code and perform the following tasks:
                        1. Identify all functions and classes in the code that require unit testing.
                        2. For each identified function or class:
                            - Generate possible test cases, categorizing each test case into one or more of the following **categories** and **subcategories** depending on the description:

                                - **Edge Cases**: Test cases that focus on extreme or boundary conditions.
                                    - Subcategories:
                                        - Boundary value analysis.
                                        - Extreme input scenarios.
                                        - Stress testing with unusual inputs.

                                - **Functional Cases**: Test cases that validate the functional requirements of the system.
                                    - Subcategories:
                                        - Core functionality testing.
                                        - Input validation testing.
                                        - Output verification testing.

                                - **Non-Functional Cases**: Test cases that validate non-functional aspects like performance, security, or scalability.
                                    - Subcategories:
                                        - Performance testing.
                                        - Security testing.
                                        - Usability testing.

                                - **Regression Cases**: Test cases that ensure new changes do not break existing functionality.
                                    - Subcategories:
                                        - Re-testing existing features.
                                        - Bug fix verification.
                                        - Side-effect testing.

                                - **Integration Tests**: Test cases that validate the interaction between different modules or systems.
                                    - Subcategories:
                                        - API integration testing.
                                        - Data flow testing.
                                        - Cross-module compatibility testing.

                                - **User Acceptance Tests (UAT)**: Test cases that validate the whole system against user requirements and ensure it meets business needs.
                                    - Subcategories:
                                        - End-to-end workflow testing.
                                        - Business requirement validation.
                                        - User experience testing.

                                - **Positive Cases**: Test cases that validate the system behaves as expected under normal or ideal conditions.
                                    - Subcategories:
                                        - Valid input testing.
                                        - Ideal scenario testing.
                                        - Expected output verification.

                                - **Negative Cases**: Test cases that validate the system handles unexpected or adverse conditions gracefully.
                                    - Subcategories:
                                        - Invalid input testing.
                                        - Error handling testing.
                                        - Exception scenario testing.

                        3. For **User Acceptance Tests (UAT)**:
                            - Generate only **one UAT test case** for the whole code.
                            - Evaluate the whole code against the provided requirements text:

                            {text_chunk.strip()}

                            - Calculate the percentage of requirements that are met by the code.
                            - Include this percentage in the output for UAT test cases.
                            - For UAT test cases, Ensure to only include the following fields:
                                - `test_case_id`
                                - `category`
                                - `test_name`
                                - `description`
                                - `requirements_met_percentage`
                            - Set all other fields to `null`.

                        4. For **Regression Cases**:
                            - Generate test cases that ensure new changes or updates do not break existing functionality.
                            - Include test cases for:
                                - Re-testing previously working features after a code change.
                                - Verifying fixes for previously reported bugs.
                            - Only include the `is_regression` field if it is `true`.

                        5. For each test case except uaT test cases:
                            - Provide detailed information, including:
                                - **Test Case ID**: A unique identifier for the test case.
                                - **Category**: The category and subcategory of the test case (e.g., "Edge Cases > Boundary value analysis").
                                - **Test Name**: A brief and descriptive name for the test case (e.g., "test_add_positive_numbers", "test_divide_by_zero").
                                - **Description**: A detailed explanation of the test case purpose.
                                - **Test Data**: Input data for the test case.
                                - **function_id**: A unique identifier for the function or class being tested.
                                - **Expected Output**: The expected outcome of the test case.
                                - **requirements_met_percentage**: The percentage of requirements met by the code (only for UAT test cases).
                                - **is_regression**: A boolean indicating if the test case is a regression test (only for Regression Cases).

                        6. Ensure that the generated test cases cover various scenarios and edge cases.
                        Do not return any explanation or comments along with the list.

                        Return the result in the following JSON format:
                        [
                            {{
                                "function": "<function_name>",
                                "function_id": "<UUID_for_function>",
                                "test_cases": [
                                    {{
                                        "test_case_id": "<UUID_for_test_case>",
                                        "category": "<category> > <subcategory>",
                                        "test_name": "<test_name>",
                                        "description": "<description>",
                                        "test_data": <test_data>,
                                        "expected_output": <expected_output>,
                                        "requirements_met_percentage": 0,  // Only for UAT test cases
                                        "is_regression": <True/False>  // Only for Regression test cases
                                    }},
                                    {{
                                        "test_case_id": "<UUID_for_test_case>",
                                        "category": "User Acceptance Tests (UAT) > <subcategory>",
                                        "test_name": "<uat_test_test_case_id>",
                                        "description": " Evaluate the whole code against the provided requirements text and return the percentage of requirements met.",
                                        "requirements_met_percentage": <percentage>,  // Only for UAT test cases
                                        "is_regression": <True/False>  // Only for Regression test cases
                                    }},
                                    ...
                                ]
                            }},
                            ...
                        ]
                        """

                        message = HumanMessage(content=prompt_template)
                        
                        try:
                            ai = ChatOpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY, temperature=0)
                            ai_response = await ai.ainvoke([message])

                            response_content = ai_response.content.strip()
                            parsed_results = json.loads(response_content)
                            
                            for item in parsed_results:
                                item["test_case_id"] = str(uuid.uuid4())

                            results.append(parsed_results)

                        except Exception as e:
                            print(f"Error during OpenAI API call unit test cases: {str(e)}")
                            results.append(f"Error processing this chunk: {str(e)}")

    flat_results = [item for sublist in results for item in sublist if isinstance(sublist, list)]
    return flat_results