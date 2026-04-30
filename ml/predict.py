import pickle
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
    return model.predict(X)[0]