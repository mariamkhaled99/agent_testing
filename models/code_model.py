from pydantic import BaseModel, UUID4
from typing import List

class UnitTest(BaseModel):
    unit_test_code: str  # The code for the unit test
    test_library: str  # The testing library/framework used (e.g., pytest, unittest)
    name_unit_test_file: str  # The name of the test file
    unit_test_id: str  # UUID for the unit test
    category: str  # Category of the test (e.g., "validation", "integration")
    is_regression: bool  
    path:str
    id: str  # UUID for the test code file

class UnitTestList(BaseModel):
    unit_tests: List[UnitTest]  # List of unit tests