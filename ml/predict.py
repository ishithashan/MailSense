"""import pickle
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load model
with open(BASE_DIR / "svm_model.pkl", "rb") as f:
    model = pickle.load(f)

with open(BASE_DIR / "vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

def classify_email(subject, body):
    text = (subject or "") + " " + (body or "")
    X = vectorizer.transform([text])
    return model.predict(X)[0]"""
import pickle
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ==============================
# Load Naive Bayes model
# ==============================
with open(BASE_DIR / "naive_bayes_model.pkl", "rb") as f:
    model = pickle.load(f)

with open(BASE_DIR / "vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# ==============================
# Clean Text (SAME as training)
# ==============================
def clean_text(text):
    text = text.lower()
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^a-z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ==============================
# Prediction Function
# ==============================
def classify_email(subject, body):
    # Same logic as training (IMPORTANT)
    text = (subject or "") * 3 + " " + (body or "")
    text = clean_text(text)

    X = vectorizer.transform([text])
    return model.predict(X)[0]