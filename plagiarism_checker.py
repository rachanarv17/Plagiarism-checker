import os
import random
import requests
import re
import time
import wikipedia
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import PyPDF2
import docx
from concurrent.futures import ThreadPoolExecutor
import os
from groq import Groq

# Setup Groq API
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

from src.model import PlagiarismModel
sbert_model = PlagiarismModel()

# Common phrases/stop-sentences to ignore in search
COMMON_BLOCKS = {
    'table of contents', 'references', 'works cited', 'bibliography', 
    'the following is', 'in this paper', 'this study aims to',
    'all rights reserved', 'terms and conditions', 'published by', 'copyright'
}

def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        elif ext == '.pdf':
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + " "
        elif ext == '.docx':
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + " "
    except Exception as e:
        print(f"Error extracting text: {e}")
    return text.strip()

def search_web_fallback(phrase):
    """Reliability v3.2: Improved search with speed-conscious fallbacks."""
    results = []
    
    # 1. wikipedia Search (Fastest)
    try:
        wiki_results = wikipedia.search(phrase, results=1)
        if wiki_results:
            results.append(wikipedia.page(wiki_results[0]).url)
    except:
        pass

    # 2. DuckDuckGo Search
    try:
        with DDGS() as ddgs:
            keyword_results = list(ddgs.text(phrase, max_results=2))
            for r in keyword_results:
                link = r.get('href') or r.get('link')
                if link:
                    results.append(link)
    except:
        pass
        
    return results

def scrape_url_content(url):
    """Ultra-Fast: Scrape with reduced timeout."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=4)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for element in soup(["script", "style", "header", "footer", "nav", "aside", "form"]):
                element.extract()
            text = soup.get_text(separator=' ')
            lines = (line.strip() for line in text.splitlines())
            text = ' '.join(chunk for chunk in lines if len(chunk) > 40) 
            return text
    except:
        pass
    return ""

def calculate_similarity(doc_text, web_text):
    if not doc_text or not web_text:
        return 0.0
    try:
        # Use new SBERT + ML architecture instead of TF-IDF
        result = sbert_model.predict_plagiarism(doc_text, web_text)
        return float(result['similarity_score'])
    except Exception as e:
        print(f"SBERT Error: {e}")
        return 0.0

def generate_ai_analysis(doc_text, web_text, matched_urls):
    if not client:
        return "AI analysis is disabled. Please check your GROQ_API_KEY."
    
    try:
        prompt = f"""
        Act as an expert plagiarism checker. 
        Analyze the following document for potential plagiarism against the provided web sources.
        
        Document excerpt:
        {doc_text[:3000]}
        
        Web source excerpt:
        {web_text[:3000]}
        
        Matched URLs: {matched_urls}
        
        Provide a concise real-time analysis report (max 3 sentences) on whether this looks like genuine original work, paraphrased content, or direct plagiarism.
        """
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-8b-8192",
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"AI analysis failed: {str(e)}"

def process_document(file_path):
    doc_text = extract_text_from_file(file_path)
    if not doc_text or len(doc_text.split()) < 5:
        return {"error": "Document too short for scan."}

    # Extract top 8 fragments for parallel checking
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', doc_text)
    phrases = [s.strip() for s in sentences if len(s.split()) >= 8][:8]
    
    unique_urls = set()
    matched_phrases = []

    # --- ULTRA-FAST PARALLEL SEARCH ---
    with ThreadPoolExecutor(max_workers=8) as executor:
        search_results = list(executor.map(search_web_fallback, phrases))
        
    for phrase, urls in zip(phrases, search_results):
        if urls:
            unique_urls.update(urls)
            matched_phrases.append({"phrase": phrase, "urls": urls})

    # --- ULTRA-FAST PARALLEL SCRAPING ---
    urls_to_scrape = list(unique_urls)[:5]
    highest_site_similarity = 0.0
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        scraped_contents = list(executor.map(scrape_url_content, urls_to_scrape))
            
    scraped_texts = []
    for content in scraped_contents:
        if content:
            site_sim = calculate_similarity(doc_text, content)
            highest_site_similarity = max(highest_site_similarity, site_sim)
            scraped_texts.append(content)
            
    combined_web_text = " ".join(scraped_texts)
    overall_similarity = calculate_similarity(doc_text, combined_web_text)
    
    # Fast Reliability Scoring
    phrase_match_ratio = (len(matched_phrases) / len(phrases)) * 100 if phrases else 0
    final_score = (max(overall_similarity, highest_site_similarity) * 0.75) + (phrase_match_ratio * 0.25)

    ai_report = ""
    if combined_web_text:
        ai_report = generate_ai_analysis(doc_text, combined_web_text, urls_to_scrape)
    else:
        ai_report = "No web sources found to compare against. Document appears to be original."

    return {
        "similarity": float(min(100.0, round(final_score, 2))),
        "matched_phrases": matched_phrases,
        "source_urls": urls_to_scrape,
        "message": "Ultra-fast precision scan completed.",
        "ai_analysis": ai_report
    }
