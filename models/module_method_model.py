from pydantic import BaseModel, UUID4
from typing import List

class CodeSnippet(BaseModel):
    id: str  # UUID for unique identification
    path: str  # Path to the function or class
    name: str  # Name of the function or class
    type: str  # Type code (e.g., "function", "class")
    code: str  # Full code snippet

class CodeSnippetList(BaseModel):
    snippets: List[CodeSnippet]  # List of code snippets