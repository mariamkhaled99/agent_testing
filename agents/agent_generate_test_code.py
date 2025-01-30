import streamlit as st
import asyncio
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from models.code_model import UnitTestList
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

# Function to analyze repository content and identify languages/frameworks

async def generate_unit_testing_code(test_cases_json: str, languages_json: str,is_regression:bool,tree=None,user_repo=None):
    print(f"tree:{tree}")
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
        function_path=test_case.get("function_path","Unknown")
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
                    framework_used = " ".join(languages["frameworks"]) if languages else "Unknown"

                    # Prepare the prompt for generating unit tests
                    prompt_template =[
                    {"role": "system", "content": "You are a professional software tester."},
                    {"role": "user", "content": f"""
                    Given the following function in {language_used}:

                    Function Name: {function_name}
                    Function ID: {function_id}
                    Function Path: {function_path}

                    Test Cases:
                    {sub_chunk.strip()}

                    Requirements:
                    - Generate unit tests for the function based on the provided test cases.
                    - Use the appropriate testing library for framework :{framework_used} and if there is no framework use the suitable library for language : {language_used} , use this library (unittest for Django, pytest for Python , Jest for javascript or nodejs).
                    - Make sure to not use any other testing library .
                    - Make sure to Import the function from the correct function path: `{function_path}`.
                    - Ensure the unit tests cover all the provided test cases, including their descriptions and expected outputs.

                    If {framework_used} contains 'Django', then:

                        1. **Test Only Existing Models and Fields:**  
                        - Generate tests only for models and fields that exist in the provided Django models.  
                        - Avoid testing or referencing non-existent models or fields.  

                        2. **Use Django's ORM Methods:**  
                        - Always use Django's ORM methods for CRUD operations:  
                            - `Model.objects.create()` to create new objects.  
                            ```python
                            instance = MyModel.objects.create(field1="value1", field2="value2")
                            ```
                            - `Model.objects.all()` to retrieve all objects from the model.  
                            ```python
                            all_instances = MyModel.objects.all()
                            self.assertEqual(all_instances.count(), expected_count)
                            ```  

                        3. **Assertions:**  
                        - Use Django's built-in assertion methods to validate behavior:  
                            ```python
                            self.assertEqual(instance.field1, "value1")
                            self.assertTrue(instance.is_active)
                            self.assertRaises(MyModel.DoesNotExist, MyModel.objects.get, id=999)
                            ```  

                        4. **View Testing:**  
                        - Only generate tests for views (functions or classes) that exist in the project.  
                        - Use Django's test client to simulate HTTP requests.  
                        - **Do not use** `reverse` from `django.urls` or manually provide URL paths.  
                            ```python
                            response = self.client.get("/existing-endpoint/")
                            self.assertEqual(response.status_code, 200)
                            ```  
                    - Include assertions to validate the expected outputs.
                    - Provide the name of the test file and its unique ID.
                    -provide the name of the test library used in the test.
                    - Ensure the code is complete and ready to be used for unit testing.
                    - Do not include any irrelevant code.
                    - Do not return any explanation or comments along with the list.
                    - Determine the root path in case of django where the manage.py exist , else is None .
                    - Determine the path of manage.py file: if {framework_used} contains Django using the project tree tructure {tree}  
                      make sure to remove the {user_repo} and the - after it from the project_root_path , make sure that project_root_path does not start with /

                    Return the result in the following JSON format:
                    
                        {{ "test_code_result": [
                            {{
                                "unit_test_code": "<unit_test_code>",
                                "test_library": "<test_library>",
                                "name_unit_test_file": "<name_of_test_file>",
                                "path":"path_test_file>",
                                "unit_test_id": "<UUID_for_unit_test>",
                                "category": "<category>",
                                "id": "<UUID_for_test_code_file>",
                                "project_root_path":"<project_root_path>",
                                
                            }},
                            ...
                        ] }}
                    """}]

                    # message = HumanMessage(content=prompt_template)
                    
                    try:
                        # Initialize OpenAI API client with error handling
                        # ai = ChatOpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY, temperature=0)
                        # ai_response = await ai.ainvoke([message])
                        
                        ai = client.beta.chat.completions.parse(model="gpt-4o-mini-2024-07-18", messages=prompt_template, response_format=UnitTestList)
                        parsed_results = ai.choices[0].message.parsed

                        print("==============================================================================================")
                        print(f"parsed_results using parser: {parsed_results}")
                        
                        # Extract test cases from parsed_results
                        
          
                        unit_tests = [
                                {
                                    "unit_test_code": snippet.unit_test_code,
                                    "test_library": snippet.test_library,
                                    "name_unit_test_file":snippet.name_unit_test_file,
                                    "category":snippet.category,
                                    "is_regression":is_regression,
                                    "path":snippet.path,
                                    "project_root_path":snippet.project_root_path,
                                    "unit_test_id":str(uuid.uuid4()),
                                    "id":str(uuid.uuid4()),
                                    
                                }
                                for snippet in parsed_results.unit_tests
                            ]

                            # Append the result to the results list
                        results.extend(unit_tests)

                    except Exception as e:
                        print(f"Error during OpenAI API call unit test code: {str(e)}")
                        results.append(f"Error processing this chunk: {str(e)}")


    # Return the aggregated results as a JSON string
    json_output = json.dumps(results, indent=4)
    print(f"json_output: {json_output}")
    return json_output
