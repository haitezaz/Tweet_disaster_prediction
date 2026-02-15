"""
train.py

Implements the model training pipeline.
This module trains machine learning models using preprocessed data
and persists trained artifacts for downstream usage.

Responsibilities:
- Initialize model configurations
- Train baseline and alternative models
- Save trained model artifacts to disk
- Log training metadata for reproducibility

No evaluation or inference logic is handled here.
"""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

from src.data_work.preprocess import preprocess_data
from src.features.feature_engineering import build_tfidf_features


def train_baseline_model(data_path):
    """
    Trains a baseline Logistic Regression model
    using TF-IDF features for Assignment 1.
    """

    # Load data
    df = pd.read_csv(data_path)

    # Preprocess data
    X, y = preprocess_data(df)

    # Train-validation split (IMPORTANT: before TF-IDF fitting)
    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    # Feature engineering (fit only on training data)
    X_train_tfidf, X_val_tfidf, vectorizer = build_tfidf_features(
        X_train, X_val
    )

    # Baseline model
    model = LogisticRegression(max_iter=1000)

    model.fit(X_train_tfidf, y_train)

    # Validation prediction
    y_pred = model.predict(X_val_tfidf)

    acc = accuracy_score(y_val, y_pred)

    print(f"Validation Accuracy: {acc:.4f}")

    return model, vectorizer


if __name__ == "__main__":
    train_baseline_model("data/raw/train.csv")
