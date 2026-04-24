import hashlib

def calculate_sha256(text: str) -> str:
    """Calculates the SHA-256 hash of the given text for integrity checking."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def verify_integrity(text: str, expected_hash: str) -> bool:
    """Verifies if the text matches the expected SHA-256 hash."""
    return calculate_sha256(text) == expected_hash
