import re

def clean_text(text: str) -> str:
    """
    Cleans the input text for better semantic analysis.
    - Removes extra whitespaces
    - Normalizes quotes
    - Basic punctuation handling
    """
    if not text:
        return ""
    
    # Remove HTML tags if any sneaked through
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Normalize whitespaces
    text = re.sub(r'\s+', ' ', text)
    
    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"').replace("'", "'").replace("'", "'")
    
    return text.strip()

def chunk_text(text: str, chunk_size: int = 5) -> list:
    """
    Splits text into chunks of roughly 'chunk_size' sentences.
    Useful for document-level embedding comparison.
    """
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', text)
    sentences = [s.strip() for s in sentences if len(s.split()) >= 3]
    
    chunks = []
    for i in range(0, len(sentences), chunk_size):
        chunk = " ".join(sentences[i:i+chunk_size])
        chunks.append(chunk)
        
    return chunks
