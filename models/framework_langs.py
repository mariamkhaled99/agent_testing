
from typing import List
from pydantic import BaseModel

class TechstackModel(BaseModel):
    languages: List[str]
    frameworks: List[str]
    