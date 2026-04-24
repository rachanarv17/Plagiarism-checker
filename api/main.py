from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

# Ensure src and security modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model import PlagiarismModel
from src.preprocessing import clean_text
from security.integrity import calculate_sha256
from security.threat_detection import detect_threats

app = FastAPI(
    title="Secure Content Integrity & Plagiarism Analyzer",
    description="Industry-ready API for semantic plagiarism detection and content security.",
    version="2.0.0"
)

# Initialize ML model globally
plagiarism_model = PlagiarismModel()

class PlagiarismRequest(BaseModel):
    document_text: str
    source_text: str

class SecurityRequest(BaseModel):
    content: str

@app.get("/")
def read_root():
    return {"message": "Welcome to Secure Content Integrity & Plagiarism Analyzer API"}

@app.post("/check-plagiarism")
def check_plagiarism(request: PlagiarismRequest):
    if not request.document_text or not request.source_text:
        raise HTTPException(status_code=400, detail="Both document_text and source_text are required.")
        
    doc_clean = clean_text(request.document_text)
    src_clean = clean_text(request.source_text)
    
    result = plagiarism_model.predict_plagiarism(doc_clean, src_clean)
    
    return {
        "status": "success",
        "data": result
    }

@app.post("/analyze-risk")
def analyze_risk(request: SecurityRequest):
    if not request.content:
        raise HTTPException(status_code=400, detail="Content is required.")
        
    content_hash = calculate_sha256(request.content)
    threat_analysis = detect_threats(request.content)
    
    return {
        "status": "success",
        "integrity_hash_sha256": content_hash,
        "security_analysis": threat_analysis
    }
