from pydantic import BaseModel, UUID4
from typing import List, Dict, Any, Union

class TestCase(BaseModel):
    test_case_id: str  # UUID for the test case
    category: str  # Category and subcategory (e.g., "category > subcategory")
    test_name: str  # Name of the test case
    description: str  # Description of the test case
    test_data: Union[str, int, float, bool, Dict[str, Any], List[Union[str, int, float, bool, Dict[str, Any]]]]  # Input test data (dynamic structure)
    expected_output: Union[str, int, float, bool, Dict[str, Any], List[Union[str, int, float, bool, Dict[str, Any]]]]
    is_regression: bool 


class CodeSnippet(BaseModel):
    function_id: str  # UUID for unique identification
    function_path: str  # Path to the function or class
    function_name: str  # Name of the function or class
    test_cases: List[TestCase]
    

class FunctionTestList(BaseModel):
    test_cases_result: List[CodeSnippet]  # List of functions with their test cases
    
    