import os
import random
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import docx

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

def generate_phrases(text, num_phrases=5, words_per_phrase=8):
    words = text.split()
    phrases = []
    if len(words) < words_per_phrase:
        return [" ".join(words)] if words else []
    
    for _ in range(num_phrases):
        start_idx = random.randint(0, len(words) - words_per_phrase)
        phrase = " ".join(words[start_idx:start_idx + words_per_phrase])
        phrases.append(phrase)
    return list(set(phrases))

def search_web_for_phrase(phrase, max_results=2):
    results = []
    try:
        with DDGS() as ddgs:
            search_results = list(ddgs.text(f'"{phrase}"', max_results=max_results))
            for r in search_results:
                if 'href' in r:
                    results.append(r['href'])
    except Exception as e:
        print(f"Error searching for {phrase}: {e}")
    return results

def scrape_url_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for element in soup(["script", "style", "header", "footer", "nav"]):
                element.extract()
            text = soup.get_text(separator=' ')
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    return ""

def calculate_similarity(doc_text, web_text):
    if not doc_text or not web_text:
        return 0.0
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([doc_text, web_text])
        sim_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return round(sim_score * 100, 2)
    except Exception as e:
        print(f"Error in similarity calculation: {e}")
        return 0.0

def process_document(file_path):
    doc_text = extract_text_from_file(file_path)
    if not doc_text:
        return {"error": "Could not extract text from document."}

    phrases = generate_phrases(doc_text, num_phrases=5, words_per_phrase=8)
    
    overall_similarity = 0.0
    matched_phrases = []
    scraped_texts = []
    
    unique_urls = set()
    
    for phrase in phrases:
        urls = search_web_for_phrase(phrase, max_results=2)
        if urls:
            unique_urls.update(urls)
            matched_phrases.append({
                "phrase": phrase,
                "urls": urls
            })

    urls_to_scrape = list(unique_urls)[:5]
    for url in urls_to_scrape:
        content = scrape_url_content(url)
        if content:
            scraped_texts.append(content)
            
    combined_web_text = " ".join(scraped_texts)
    
    if combined_web_text:
        overall_similarity = calculate_similarity(doc_text, combined_web_text)
    
    if len(matched_phrases) > 0 and overall_similarity < 10.0:
         overall_similarity += len(matched_phrases) * 5.0

    return {
        "similarity": min(100.0, round(overall_similarity, 2)),
        "matched_phrases": matched_phrases,
        "source_urls": urls_to_scrape,
        "message": "Scan completed successfully."
    }
