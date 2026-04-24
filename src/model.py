import os
import joblib
import numpy as np
from sentence_transformers import SentenceTransformer, util

class PlagiarismModel:
    def __init__(self, model_name='all-MiniLM-L6-v2', clf_path='models/clf_model.joblib'):
        """
        Initializes the Sentence-BERT model and the classification model (e.g., Logistic Regression).
        """
        self.sbert = SentenceTransformer(model_name)
        self.clf_path = clf_path
        self.clf = None
        
        # Load classifier if exists
        if os.path.exists(self.clf_path):
            self.clf = joblib.load(self.clf_path)

    def get_embeddings(self, texts: list):
        """Returns SBERT embeddings for a list of texts."""
        return self.sbert.encode(texts, convert_to_tensor=True)

    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculates cosine similarity between two texts.
        Returns a float between 0 and 100.
        """
        emb1 = self.sbert.encode(text1, convert_to_tensor=True)
        emb2 = self.sbert.encode(text2, convert_to_tensor=True)
        cosine_score = util.cos_sim(emb1, emb2)[0][0].item()
        return max(0.0, min(100.0, cosine_score * 100))

    def predict_plagiarism(self, text1: str, text2: str) -> dict:
        """
        Uses SBERT embeddings and a trained classifier to detect paraphrased plagiarism.
        If classifier isn't trained yet, falls back to semantic similarity thresholding.
        """
        sim_score = self.calculate_semantic_similarity(text1, text2)
        
        if self.clf is None:
            # Fallback heuristic if no ML classifier is trained yet
            is_plagiarized = sim_score > 75.0
            confidence = sim_score if is_plagiarized else (100 - sim_score)
            return {
                "label": "Plagiarized" if is_plagiarized else "Original",
                "similarity_score": round(sim_score, 2),
                "confidence": round(confidence, 2)
            }
            
        # If classifier exists, compute feature differences
        emb1 = self.sbert.encode(text1)
        emb2 = self.sbert.encode(text2)
        
        # Feature: Absolute difference + element-wise product (common strategy for NLI/Similarity)
        features = np.abs(emb1 - emb2)
        features = np.concatenate([features, emb1 * emb2]).reshape(1, -1)
        
        pred = self.clf.predict(features)[0]
        prob = self.clf.predict_proba(features)[0]
        confidence = max(prob) * 100
        
        return {
            "label": "Plagiarized" if pred == 1 else "Original",
            "similarity_score": round(sim_score, 2),
            "confidence": round(confidence, 2)
        }
