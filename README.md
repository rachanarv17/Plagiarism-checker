# Plagiarism Detection System 🔍

A full-stack, web-based plagiarism detection application built using **Python, Flask, and Vanilla CSS**. This system empowers users to easily verify the originality of their documents by cross-referencing text with live web resources.

## Features ✨
- **Multi-Format Support:** Upload `.txt`, `.pdf`, and `.docx` files directly into the application.
- **Smart Web Scraping:** Extracts raw text, generates random structural phrases, and compares them against web results using `duckduckgo-search` and `BeautifulSoup`.
- **Intelligent Analytics:** Calculates exact phrase similarities alongside overarching Term Frequency-Inverse Document Frequency (TF-IDF) scoring via `scikit-learn`.
- **Premium UI/UX:** A highly responsive dashboard boasting frosted glass-morphism, custom circular chart animations, and a polished dark-mode interface.
- **Reporting:** Instantly generate and download PDF summary reports for your scans.
- **Authentication:** Built-in user sign-up and login securely managed by SQLite + SQLAlchemy.

## Technologies Used 💻
- **Backend:** Python 3, Flask, SQLAlchemy 
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla API Integration)
- **NLP / Searching:** Scikit-Learn, DuckDuckGo-Search, BeautifulSoup4
- **PDF Generation:** FPDF2

## Setup Instructions 🚀

To test this project locally, clone this repository and follow the steps below:

**1. Create a Virtual Environment (Optional but Recommended)**
```bash
python -m venv venv
```
Activate it:
* **Windows:** `venv\Scripts\activate`
* **Mac/Linux:** `source venv/bin/activate`

**2. Install Requirements**
```bash
pip install -r requirements.txt
```

**3. Run the Server**
```bash
python app.py
```

**4. Access the Platform**
Open your web browser and navigate to: `http://localhost:5000`

## Author
Developed by Rachana RV.
