<div align="center">

<img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Flask-2.x-000000?style=for-the-badge&logo=flask&logoColor=white"/>
<img src="https://img.shields.io/badge/Scikit--Learn-ML-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white"/>
<img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
<img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/>

<br/><br/>

# 🔍 AuthentiCheck — Plagiarism Detection System

### *An intelligent, full-stack document originality verification platform powered by NLP and real-time web analysis.*

<br/>

> Upload any document — get a precise similarity score, flagged phrases, and matching source URLs in seconds.

<br/>

</div>

---

## 📌 Table of Contents

- [🔍 Overview](#-overview)
- [✨ Features](#-features)
- [🏗 System Architecture](#-system-architecture)
- [🧠 NLP Processing Pipeline](#-nlp-processing-pipeline)
- [💻 Technology Stack](#-technology-stack)
- [📁 Project Structure](#-project-structure)
- [🚀 Setup & Installation](#-setup--installation)
- [💡 Usage Workflow](#-usage-workflow)
- [📸 UI Highlights](#-ui-highlights)
- [👩‍💻 Author](#-author)

---

## 🔍 Overview

**AuthentiCheck** is a production-grade plagiarism detection web application built using Python and Flask. It enables users to instantly assess the originality of their documents by intelligently cross-referencing extracted text against live web sources using a parallelized NLP pipeline.

Whether you're an academic, content creator, or developer, AuthentiCheck delivers fast, precise, and readable results — all packaged in a premium, glassmorphic dark-mode UI.

---

## ✨ Features

| Feature | Description |
|:---|:---|
| 📄 **Multi-Format Parsing** | Supports `.txt`, `.pdf`, and `.docx` document uploads |
| ⚡ **Parallel Web Search** | Concurrent searches via DuckDuckGo & Wikipedia using `ThreadPoolExecutor` |
| 🧠 **TF-IDF Similarity Engine** | Cosine similarity scoring using `scikit-learn` for precise originality analysis |
| 🌐 **Smart Web Scraping** | `BeautifulSoup4` efficiently strips boilerplate and extracts clean web content |
| 📊 **Visual Analytics** | Animated circular similarity gauge with color-coded risk levels |
| 📝 **PDF Report Export** | Instant, downloadable detailed scan reports via `FPDF2` |
| 🔐 **Secure Authentication** | Session-based login system with hashed passwords via `werkzeug` + `SQLAlchemy` |
| ☁️ **Vercel Compatible** | Serverless-ready with `/tmp` path fallbacks for cloud deployment |

---

## 🏗 System Architecture

The application follows a **Client–Server architecture** with a parallelized backend processing pipeline:

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                               │
│                                                                     │
│   Browser  ──►  HTML/CSS/JS UI  ──►  File Upload / Results View    │
└────────────────────────────┬────────────────────────────────────────┘
                             │  HTTP POST (multipart/form-data)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FLASK SERVER (app.py)                        │
│                                                                     │
│   /login   /signup   /logout   /api/scan   /report                 │
│                         │                                           │
│              ┌──────────▼──────────┐                               │
│              │   File Processor    │  PyPDF2 / python-docx / open() │
│              └──────────┬──────────┘                               │
│                         │ Extracted Plain Text                      │
│              ┌──────────▼──────────┐                               │
│              │  Sentence Chunker   │  regex-based NLP tokenizer     │
│              └──────────┬──────────┘                               │
│                         │ Top 8 Meaningful Phrases                  │
└─────────────────────────┼───────────────────────────────────────────┘
                          │
         ┌────────────────┼───────────────────┐
         │                │                   │
         ▼                ▼                   ▼
┌────────────────┐ ┌─────────────┐ ┌─────────────────────┐
│ DuckDuckGo API │ │ Wikipedia   │ │  ThreadPoolExecutor  │
│  (Web Search)  │ │ (Fast Wiki) │ │  (8 parallel tasks)  │
└───────┬────────┘ └──────┬──────┘ └──────────┬──────────┘
        └────────────┬────┘                    │
                     ▼                         │
          ┌──────────────────┐                 │
          │  URL Aggregator  │◄────────────────┘
          └────────┬─────────┘
                   │ Top 5 Source URLs
                   ▼
          ┌──────────────────┐
          │  Web Scraper     │  BeautifulSoup4 (parallel)
          │  (5 concurrent)  │  Removes nav/footer/scripts
          └────────┬─────────┘
                   │ Clean Web Text
                   ▼
┌──────────────────────────────────────────────────┐
│             MACHINE LEARNING CORE                │
│                                                  │
│  TF-IDF Vectorizer  ──►  Cosine Similarity       │
│  (ngram_range 1–2)       (doc vs. web text)      │
│                                                  │
│  Final Score = (max_similarity × 0.75)           │
│              + (phrase_match_ratio × 0.25)        │
└─────────────────────┬────────────────────────────┘
                      │ JSON Response
                      ▼
             ┌─────────────────┐
             │  Flask Response │──► Frontend UI + PDF Report
             └─────────────────┘
```

---

## 🧠 NLP Processing Pipeline

```
Document Upload
      │
      ▼
Text Extraction  ──────────────────────┐
(PyPDF2 / docx / plain text)          │
      │                                │
      ▼                                ▼
Sentence Tokenization            Chunk Validation
(regex split on ". " / "? ")    (min 8 words per phrase)
      │
      ▼
Parallel Web Search (ThreadPoolExecutor × 8)
      │
      ├──► DuckDuckGo Search (max 2 results per phrase)
      └──► Wikipedia Search  (max 1 result per phrase)
                │
                ▼
        URL Deduplication & Collection
                │
                ▼
Parallel Web Scraping (ThreadPoolExecutor × 5)
        │
        ▼
BeautifulSoup4 Content Extraction
(strips: script, style, nav, footer, aside, form)
        │
        ▼
TF-IDF Vectorization (unigrams + bigrams, English stopwords removed)
        │
        ▼
Cosine Similarity → Per-site score + Combined aggregate score
        │
        ▼
Final Weighted Scoring:
  → 75% from max TF-IDF cosine similarity
  → 25% from phrase match hit ratio
        │
        ▼
JSON Result  { similarity, matched_phrases, source_urls }
```

---

## 💻 Technology Stack

| Layer | Technology | Purpose |
|:---|:---|:---|
| **Web Framework** | Flask 2.x | REST routing, session management, templating |
| **Frontend** | HTML5, CSS3, JavaScript | Glassmorphic UI, animated charts, file upload |
| **NLP / ML** | Scikit-Learn | TF-IDF vectorization & cosine similarity scoring |
| **Web Search** | DuckDuckGo-Search, Wikipedia API | Live source URL discovery |
| **Web Scraping** | BeautifulSoup4, Requests | Structured content extraction from web pages |
| **File Parsing** | PyPDF2, python-docx | Document text extraction |
| **PDF Export** | FPDF2 | On-the-fly plagiarism report generation |
| **Database** | SQLite3 + SQLAlchemy | User authentication & session persistence |
| **Security** | Werkzeug | Password hashing & secure session tokens |
| **Concurrency** | ThreadPoolExecutor | Parallel searching and scraping |

---

## 📁 Project Structure

```
plagiarism-checker/
│
├── app.py                      # 🚀 Flask app entry point, all routes & PDF logic
├── plagiarism_checker.py       # 🧠 Core NLP pipeline (search, scrape, score)
├── requirements.txt            # 📦 All Python dependencies
│
├── templates/
│   ├── auth.html               # 🔐 Login & Signup page (Jinja2 template)
│   └── index.html              # 📊 Main dashboard with upload & results
│
├── static/
│   ├── css/
│   │   └── style.css           # 🎨 Glassmorphism dark-mode styles & animations
│   └── js/
│       └── main.js             # ⚙️  Async file upload, results rendering, charts
│
├── instance/
│   └── users.db                # 🗄️  Auto-generated SQLite database
│
├── uploads/                    # 📂 Temp storage for uploads & generated PDF reports
├── inspect_ddgs.py             # 🔧 DuckDuckGo API inspection utility
└── test_debug.py               # 🧪 Local debug & testing script
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.8 or higher
- `pip` package manager
- Internet connection (for web search features)

### Step 1 — Clone the Repository
```bash
git clone https://github.com/rachanarv17/Plagiarism-checker.git
cd Plagiarism-checker
```

### Step 2 — Create a Virtual Environment *(Recommended)*
```bash
# Create the environment
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — macOS / Linux
source venv/bin/activate
```

### Step 3 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Start the Application
```bash
python app.py
```

### Step 5 — Open in Browser
```
http://127.0.0.1:10000
```

---

## 💡 Usage Workflow

```
1. Sign Up / Login     →  Create an account or log into the secure portal
         │
         ▼
2. Upload Document     →  Select a .txt, .pdf, or .docx file to scan
         │
         ▼
3. Scan & Analyze      →  Backend parallelizes search + scraping in real-time
         │
         ▼
4. View Results        →  Similarity score, flagged phrases & source URLs shown
         │
         ▼
5. Download Report     →  Export a full PDF plagiarism report instantly
```

---

## 📸 UI Highlights

- 🌑 **Dark glassmorphism dashboard** with frosted panel effects
- 🔵 **Animated circular score gauge** with gradient strokes
- ⚠️ **Color-coded risk indicators** (green / orange / red)
- 📎 **Drag-and-drop file upload** with live filename preview
- 📱 **Fully responsive layout** — works on desktop and mobile

---

## 👩‍💻 Author

<div align="center">

**Designed & Developed with ❤️ by Rachana RV**

[![GitHub](https://img.shields.io/badge/GitHub-rachanarv17-181717?style=for-the-badge&logo=github)](https://github.com/rachanarv17)

</div>
