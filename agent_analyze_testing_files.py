import streamlit as st
import asyncio
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from utils import count_tokens, split_into_chunks, split_large_chunk
from dotenv import load_dotenv
import os


load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_CHUNK_SIZE = 100000  # Define a safe chunk size to avoid token overflow
MAX_TOKENS = 16000  # Safe limit for gpt-3.5-turbo
RESERVED_PROMPT_TOKENS = 1000  # Reserve tokens for the prompt

# Function to analyze repository content and identify languages/frameworks

async def analyze_repo_content_need_testing(content: str):
    # Define safe token limit for content chunks
    safe_token_limit = MAX_TOKENS - RESERVED_PROMPT_TOKENS
    
    # Split content into manageable chunks
    chunks = split_into_chunks(content, safe_token_limit)
    results = []

    for chunk in chunks:
        # Further split if a chunk exceeds the safe token limit
        if count_tokens(chunk) > safe_token_limit:
            smaller_chunks = split_large_chunk(chunk, safe_token_limit)
        else:
            smaller_chunks = [chunk]

        for sub_chunk in smaller_chunks:
            if sub_chunk.strip():  # Skip empty chunks
                prompt_template = f"""
                Given this content of code: {sub_chunk.strip()} of this project, analyze the code to identify functions, classes, and modules that require testing.

                Requirements:
                - List the names and types of functions, classes, and modules that require testing.
                - Return the **full code snippet** for each identified item.
                - Do not include any explanation or comments.
                - Do not include code that does not require testing.
                - Ensure the code for each function, class, or module is complete.

                Return the result in the following format:
                [
                    {{
                        "name": "function_or_class_or_module_name",
                        "type": "type_code",
                        "code": "full_code_snippet"
                    }},
                    ...
                ]
                """


                message = HumanMessage(content=prompt_template)
                
                try:
                    # Initialize OpenAI API client with error handling
                    ai = ChatOpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY, temperature=0)
                    ai_response = await ai.ainvoke([message])
                    results.append(ai_response.content.strip())
                
                except Exception as e:
                    print(f"Error during OpenAI API call: {str(e)}")
                    results.append(f"Error processing this sub-chunk: {str(e)}")
    
    return "\n".join(results)

