import re

def detect_threats(text: str) -> dict:
    """
    Detects malicious patterns in text like script tags, SQL injection patterns,
    or suspicious URLs.
    """
    threats = []
    
    # Check for script tags
    if re.search(r'<\s*script.*?>.*?</\s*script\s*>', text, re.IGNORECASE | re.DOTALL):
        threats.append("Cross-Site Scripting (XSS) payload detected (<script> tags).")
        
    # Check for basic SQL Injection patterns
    sql_patterns = [
        r"(?i)\bSELECT\b.*\bFROM\b",
        r"(?i)\bDROP\b\s+\bTABLE\b",
        r"(?i)\bUNION\b.*\bSELECT\b",
        r"['\"];\s*(?:DROP|SELECT|INSERT|UPDATE|DELETE)\b"
    ]
    for pattern in sql_patterns:
        if re.search(pattern, text):
            threats.append(f"Potential SQL Injection pattern detected.")
            break
            
    # Check for suspicious URLs/executables
    if re.search(r'(?i)http[s]?://.*\.(exe|bat|sh|cmd|vbs)', text):
        threats.append("Suspicious executable URL detected.")

    risk_level = "Low"
    if len(threats) >= 2:
        risk_level = "High"
    elif len(threats) == 1:
        risk_level = "Medium"
        
    return {
        "risk_level": risk_level,
        "threats": threats,
        "is_safe": len(threats) == 0
    }
