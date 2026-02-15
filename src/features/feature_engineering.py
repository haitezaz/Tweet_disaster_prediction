"""
feature_engineering.py

Contains logic for feature transformation and feature construction.
This module is responsible for improving data representation for
model performance while keeping feature logic separate from modeling.

Responsibilities:
- Create derived features
- Drop irrelevant or redundant features
- Apply domain-specific feature rules (if any)

Feature engineering decisions are explicitly defined to support
traceability and reproducibility.
"""

from sklearn.feature_extraction.text import TfidfVectorizer

def build_tfidf_features(X_train, X_val=None):
    """
    Converts cleaned text into TF-IDF feature vectors.

    Parameters:
    - X_train: training text data
    - X_val: optional validation text data

    Returns:
    - X_train_tfidf
    - X_val_tfidf (if provided)
    - fitted TF-IDF vectorizer
    """
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        stop_words="english"
    )

    X_train_tfidf = vectorizer.fit_transform(X_train)

    if X_val is not None:
        X_val_tfidf = vectorizer.transform(X_val)
        return X_train_tfidf, X_val_tfidf, vectorizer

    return X_train_tfidf, vectorizer
