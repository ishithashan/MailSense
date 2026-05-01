"""import pandas as pd
import pickle

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

# Load dataset
df = pd.read_csv("../training_data.csv")

# Prepare data
X_text = df["text"]
y = df["category"]

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

print("✅ Model trained successfully")"""
import pandas as pd
import pickle
import re

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report
from sklearn.utils import resample

# ==============================
# 1. Load Dataset
# ==============================
df = pd.read_csv("../training_data.csv")

# ==============================
# 2. Combine Subject + Body (if available)
# ==============================
if 'subject' in df.columns and 'body' in df.columns:
    df['text'] = (df['subject'].astype(str) + " ") * 3 + df['body'].astype(str)
else:
    df['text'] = df['text'].astype(str)

# ==============================
# 3. Clean Text
# ==============================
def clean_text(text):
    text = text.lower()
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^a-z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df['clean_text'] = df['text'].apply(clean_text)

# ==============================
# 4. Balance Dataset
# ==============================
max_size = df['category'].value_counts().max()

df_balanced = df.groupby('category').apply(
    lambda x: resample(x, replace=True, n_samples=max_size, random_state=42)
).reset_index(drop=True)

# ==============================
# 5. Features & categorys
# ==============================
X = df_balanced['clean_text']
y = df_balanced['category']

# ==============================
# 6. TF-IDF
# ==============================
vectorizer = TfidfVectorizer(
    stop_words='english',
    ngram_range=(1, 2),
    min_df=2
)

X_tfidf = vectorizer.fit_transform(X)

# ==============================
# 7. Train-Test Split
# ==============================
X_train, X_test, y_train, y_test = train_test_split(
    X_tfidf, y, test_size=0.2, random_state=42
)

# ==============================
# 8. Train Naive Bayes Model
# ==============================
model = MultinomialNB()
model.fit(X_train, y_train)

# ==============================
# 9. Evaluation
# ==============================
y_pred = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))

# ==============================
# 10. Cross Validation
# ==============================
scores = cross_val_score(model, X_tfidf, y, cv=5)
print("\nCross-validation Accuracy:", scores.mean())

# ==============================
# 11. Save Model & Vectorizer
# ==============================
with open("naive_bayes_model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("\n✅ Naive Bayes model trained and saved successfully!")