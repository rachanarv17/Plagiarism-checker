import os
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sentence_transformers import SentenceTransformer

def generate_synthetic_data(num_samples=200):
    """
    Generates synthetic dataset for training the classifier.
    In a real scenario, this would load from a dataset like PAWS or MRPC.
    """
    print("Generating synthetic data...")
    # 1: Plagiarized/Paraphrased, 0: Original/Different
    data = [
        ("The quick brown fox jumps over the lazy dog.", "A fast brown fox leaps over a sleepy dog.", 1),
        ("Machine learning is a field of artificial intelligence.", "AI encompasses machine learning techniques.", 1),
        ("I love eating pizza with extra cheese.", "My favorite food is cheese pizza.", 1),
        ("The quick brown fox jumps over the lazy dog.", "Quantum physics studies subatomic particles.", 0),
        ("Machine learning is a field of artificial intelligence.", "The weather today is sunny and warm.", 0),
        ("I love eating pizza with extra cheese.", "Cars are primarily used for transportation.", 0),
    ]
    
    # Duplicate and slightly modify to create a small batch
    X_pairs = []
    y = []
    for _ in range(num_samples // len(data)):
        for t1, t2, label in data:
            X_pairs.append((t1, t2))
            y.append(label)
            
    return X_pairs, np.array(y)

def train_and_evaluate():
    sbert = SentenceTransformer('all-MiniLM-L6-v2')
    X_pairs, y = generate_synthetic_data(200)
    
    print("Extracting SBERT embeddings...")
    features = []
    for t1, t2 in X_pairs:
        emb1 = sbert.encode(t1)
        emb2 = sbert.encode(t2)
        # Combine embeddings: |u - v| and u * v
        feat = np.concatenate([np.abs(emb1 - emb2), emb1 * emb2])
        features.append(feat)
        
    X = np.array(features)
    
    # Split 80/20 manually for simplicity
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    print("Training Logistic Regression Model...")
    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, y_train)
    
    print("Evaluating Model...")
    y_pred = clf.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    print("\n--- Evaluation Metrics ---")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    
    os.makedirs("models", exist_ok=True)
    model_path = "models/clf_model.joblib"
    joblib.dump(clf, model_path)
    print(f"\nModel saved to {model_path}")

if __name__ == "__main__":
    train_and_evaluate()
