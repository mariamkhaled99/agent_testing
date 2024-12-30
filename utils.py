import re
from tiktoken import encoding_for_model
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
