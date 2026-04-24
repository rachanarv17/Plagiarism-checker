# Secure Content Integrity & Plagiarism Analyzer

An industry-ready, cybersecurity-focused system for deep semantic plagiarism detection and text integrity analysis.

## Features

- **Semantic Plagiarism Detection:** Uses `Sentence-BERT` (all-MiniLM-L6-v2) combined with a Logistic Regression classifier to detect paraphrased content, moving beyond simple TF-IDF word matching.
- **Content Integrity Verification:** Uses SHA-256 hashing to generate immutable signatures for documents.
- **Cybersecurity Threat Detection:** Scans input text for Cross-Site Scripting (XSS), SQL Injection patterns, and malicious URLs before processing.
- **Modern Backend:** Built with FastAPI for high performance, automatic interactive documentation (Swagger UI), and async support.

## Architecture

```
.
├── api/
│   └── main.py              # FastAPI application and endpoints
├── security/
│   ├── integrity.py         # SHA-256 hashing functions
│   └── threat_detection.py  # Regex-based malicious pattern scanning
├── src/
│   ├── model.py             # SBERT embedding generation and ML classification
│   ├── preprocessing.py     # Text cleaning and chunking
│   └── train.py             # Script to train classifier and output evaluation metrics
├── models/                  # Saved ML models (e.g., joblib files)
└── requirements.txt
```

## Setup & Installation

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Train the Classification Model:**
   Generate the evaluation metrics (Accuracy, Precision, Recall, F1) and save the model:
   ```bash
   python src/train.py
   ```

3. **Run the API Server:**
   ```bash
   uvicorn api.main:app --reload
   ```

4. **Access the Documentation:**
   Open your browser and navigate to `http://127.0.0.1:8000/docs` to test the API interactively.

## API Endpoints

### `POST /check-plagiarism`
Analyzes two text inputs for semantic similarity and paraphrased plagiarism.
**Payload:**
```json
{
  "document_text": "The quick brown fox jumps over the lazy dog.",
  "source_text": "A fast brown fox leaps over a sleepy dog."
}
```

### `POST /analyze-risk`
Scans text for security threats and generates a SHA-256 integrity hash.
**Payload:**
```json
{
  "content": "Check out my new website <script>alert(1)</script>"
}
```
