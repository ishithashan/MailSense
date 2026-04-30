import pandas as pd
import pickle

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

# Load dataset
df = pd.read_csv("../training_data.csv")

# Prepare data
X_text = df["text"]
y = df["label"]

# Convert text → vectors
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(X_text)

# Train model
model = LinearSVC()
model.fit(X, y)

# Save model
with open("svm_model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("✅ Model trained successfully")