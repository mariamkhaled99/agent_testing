import re
from tiktoken import encoding_for_model
from urllib.parse import urlparse
# Function to count tokens
def count_tokens(text, model="gpt-3.5-turbo"):
    enc = encoding_for_model(model)
    return len(enc.encode(text))

def split_large_chunk(chunk, max_chunk_tokens, model="gpt-3.5-turbo"):
    """
    Split a chunk into smaller parts if it exceeds the token limit.
    """
    enc = encoding_for_model(model)
    encoded = enc.encode(chunk)
    split_chunks = [
        enc.decode(encoded[i:i + max_chunk_tokens])
        for i in range(0, len(encoded), max_chunk_tokens)
    ]
    return split_chunks
def split_into_chunks(text, max_size):
        """
        Split text into manageable chunks by logical delimiters and enforce token limits.
        """
        chunks = []
        current_chunk = []
        current_size = 0

        sections = re.split(r'(\n={60,}\nFile: [^\n]+)', text)
        for section in sections:
            section_size = count_tokens(section)
            if current_size + section_size > max_size:
                if current_chunk:
                    chunks.append("".join(current_chunk))
                current_chunk = [section]
                current_size = section_size
            else:
                current_chunk.append(section)
                current_size += section_size

        if current_chunk:
            chunks.append("".join(current_chunk))

        return chunks
    
def get_repo_name(url):
    # Parse the URL
    parsed_url = urlparse(url)
    
    # Split the path to get the parts
    path_parts = parsed_url.path.strip('/').split('/')
    
    # The repository name is the second part of the path
    if len(path_parts) >= 2:
        return path_parts[1]
    else:
        return None    
   
   
