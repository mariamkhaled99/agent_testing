import streamlit as st
import asyncio
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from models.cases_model import FunctionTestList
from utils import count_tokens, split_into_chunks, split_large_chunk
from dotenv import load_dotenv
import os
import uuid
import json
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_CHUNK_SIZE = 100000  # Define a safe chunk size to avoid token overflow
MAX_TOKENS = 16000  # Safe limit for gpt-3.5-turbo
RESERVED_PROMPT_TOKENS = 1000  # Reserve tokens for the prompt
client = OpenAI()

async def generate_test_cases(modules_need_testing_json: str, languages_json: str, extracted_text: str,is_regression:bool):
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
    # extracted_text_chunks=None
    if not extracted_text_chunks:
        text_chunk="relay on the code "
        
    results = []

    for module in modules:
        chunks = split_into_chunks(module['code'], safe_token_limit)
        function_path=module.get("path","Unknown")

        for chunk in chunks:
            if count_tokens(chunk) > safe_token_limit:
                smaller_chunks = split_large_chunk(chunk, safe_token_limit)
            else:
                smaller_chunks = [chunk]

            for sub_chunk in smaller_chunks:
                if sub_chunk.strip():
                    language_used = " ".join(languages["languages"]) if languages else "Unknown"

                    for text_chunk in extracted_text_chunks:
                        prompt_template = [
                        {"role": "system", "content": "You are a professional software tester."},
                        {"role": "user", "content":f"""
                            Given the following code written in {language_used}:

                        

                            Analyze the provided code and perform the following tasks:
                            1. For all the Identified  functions and classes in the code that require unit testing {sub_chunk.strip()}.
                            2. Compare the identified functions and classes against the provided requirements text: {text_chunk.strip()}
                            3.Generate test cases specific to how these functions and classes fulfill or interact with the provided requirements.
                            4. Generate possible test cases, categorizing each test case into the following **categories** and **subcategories** depending on the description:

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


                            5. For each test case :
                                - Provide detailed information, including:
                                    - **Test Case ID**: A unique identifier for the test case.
                                    - **Category**: The category and subcategory of the test case (e.g., "Edge Cases > Boundary value analysis").
                                    - **Test Name**: A brief and descriptive name for the test case (e.g., "test_add_positive_numbers", "test_divide_by_zero").
                                    - **Description**: A detailed explanation of the test case purpose.
                                    - **Test Data**: Input data for the test case.
                                    - **function_id**: A unique identifier for the function or class being tested.
                                    - **function_path**:specifies the location of the function or class being tested within the codebase {function_path}. so It is used to generate the correct import statement in the unit test code, ensuring that the tests can access the function or class being tested.
                                    - **Expected Output**: The expected outcome of the test case.
                                    - **requirements_met_percentage**: The percentage of requirements met by the code (only for UAT test cases).
                                    - **is_regression**: A boolean indicating if the test case is a regression test (only for Regression Cases).

                            6. Ensure that the generated test cases cover various scenarios and edge cases.
                            Do not return any explanation or comments along with the list.

                            Return the result in the following JSON format:
                                    {{
                                        "test_cases_result": [
                                            {{
                                                "function": "<function_name>",
                                                "function_id": "<UUID_for_function>",
                                                "function_path":"<function_path>",
                                                "test_cases": [
                                                    {{
                                                        "test_case_id": "<UUID_for_test_case>",
                                                        "category": "<category> > <subcategory>",
                                                        "test_name": "<test_name>",
                                                        "description": "<description>",
                                                        "test_data": <test_data>,
                                                        "expected_output": <expected_output>,
                                                        "is_regression": <is_regression>
                                                    }}
                                                ]
                                            }}
                                        ]
                                    }}
                            """}]

                        # message = HumanMessage(content=prompt_template)
                        
                    try:
                        ai = client.beta.chat.completions.parse(model="gpt-4o-mini-2024-07-18", messages=prompt_template, response_format=FunctionTestList)
                        parsed_results = ai.choices[0].message.parsed

                        print("==============================================================================================")
                        print(f"parsed_results using parser: {parsed_results}")

                        # Extract test cases from parsed_results
                        test_cases_result = [
                            {
                                "function": snippet.function_name,
                                "function_id": str(uuid.uuid4()),
                                "function_path":snippet.function_path,
                                "test_cases": [
                                    {
                                        "test_case_id": str(uuid.uuid4()),
                                        "category": test_case.category,
                                        "test_name": test_case.test_name,
                                        "description": test_case.description,
                                        "test_data": test_case.test_data,
                                        "expected_output": test_case.expected_output,
                                        "is_regression": is_regression,
                                    }
                                    for test_case in snippet.test_cases
                                ],
                            }
                            for snippet in parsed_results.test_cases_result
                        ]

                        # Append the result to the results list
                        results.extend(test_cases_result)

                    except Exception as e:
                        print(f"Error during OpenAI API call unit test cases: {str(e)}")
                        results.append({"error": f"Error processing this chunk: {str(e)}"})

    # Return the aggregated results as a JSON string
    json_output = json.dumps(results, indent=4)
    print(f"json_output: {json_output}")
    return json_output


   