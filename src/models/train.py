"""
train.py

Implements the model training pipeline.

Responsibilities:
- Load and preprocess dataset
- Perform train/validation split with leakage prevention
- Train multiple classification models
- Evaluate models using dedicated evaluation module
- Perform structured error analysis
- Return trained artifacts for downstream usage

Note:
This module does NOT handle inference logic.
Prediction is handled separately in predict.py.
"""
import numpy as np
import random
import joblib

from src.config import RANDOM_SEED, TEST_SIZE, LR_MAX_ITER

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB

from src.data_work.preprocess import preprocess_data
from src.features.feature_engineering import build_tfidf_features
from src.models.evaluate import evaluate_model
from src.models.error_analysis import analyze_errors


def train_models(data_path):
    """
    Trains baseline and alternative models using TF-IDF features.
    Returns trained models, metrics, and vectorizer.
    """

    # Load dataset
    df = pd.read_csv(data_path)

    # Preprocess data
    X, y = preprocess_data(df)

    # Train-validation split (before vectorization to avoid leakage)
    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_SEED,
        stratify=y
    )

    # Feature engineering
    X_train_tfidf, X_val_tfidf, vectorizer = build_tfidf_features(
        X_train, X_val
    )

    results = {}

    # ==============================
    # Logistic Regression (Primary)
    # ==============================

    print("\n==============================")
    print("Training Logistic Regression")
    print("==============================")

    lr_model = LogisticRegression(max_iter=LR_MAX_ITER, random_state=RANDOM_SEED)
    lr_model.fit(X_train_tfidf, y_train)

    lr_metrics = evaluate_model(lr_model, X_val_tfidf, y_val)

    print("\nPerforming Error Analysis for Logistic Regression")
    lr_errors = analyze_errors(
        lr_model,
        X_val_tfidf,
        y_val,
        X_val
    )

    results["logistic_regression"] = {
        "model": lr_model,
        "metrics": lr_metrics,
        "errors": lr_errors
    }

    # ==============================
    # Multinomial Naive Bayes
    # ==============================

    print("\n==============================")
    print("Training Multinomial Naive Bayes")
    print("==============================")

    nb_model = MultinomialNB()
    nb_model.fit(X_train_tfidf, y_train)

    nb_metrics = evaluate_model(nb_model, X_val_tfidf, y_val)

    results["naive_bayes"] = {
        "model": nb_model,
        "metrics": nb_metrics
    }

    results["vectorizer"] = vectorizer

        # ==============================
    # Save Artifacts
    # ==============================

    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    joblib.dump(lr_model, artifacts_dir / "logistic_regression.pkl")
    joblib.dump(nb_model, artifacts_dir / "naive_bayes.pkl")
    joblib.dump(vectorizer, artifacts_dir / "tfidf_vectorizer.pkl")

    print("\nModels and vectorizer saved to 'artifacts/' directory.")

    return results


if __name__ == "__main__":
    train_models("data/raw/train.csv")