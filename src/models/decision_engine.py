"""
decision_engine.py

Implements confidence-aware decision logic with fallback model.

Responsibilities:
- Load serialized artifacts
- Compute prediction probabilities
- Apply confidence thresholds
- Invoke fallback model when necessary
- Return structured decision output
"""

import joblib
from pathlib import Path


class DecisionEngine:
    def __init__(self, artifacts_path="artifacts"):
        artifacts_dir = Path(artifacts_path)

        self.lr_model = joblib.load(artifacts_dir / "logistic_regression.pkl")
        self.nb_model = joblib.load(artifacts_dir / "naive_bayes.pkl")
        self.vectorizer = joblib.load(artifacts_dir / "tfidf_vectorizer.pkl")

        # Confidence thresholds
        self.high_conf_threshold = 0.75
        self.low_conf_threshold = 0.25

    def predict(self, text: str):
        """
        Returns structured prediction using confidence-aware fallback logic.
        """

        # Vectorize input
        X = self.vectorizer.transform([text])

        # Logistic Regression probability
        lr_prob = self.lr_model.predict_proba(X)[0][1]
        lr_pred = 1 if lr_prob >= 0.5 else 0

        # High confidence disaster
        if lr_prob >= self.high_conf_threshold:
            return {
                "prediction": 1,
                "confidence": float(lr_prob),
                "source": "logistic_regression"
            }

        # High confidence non-disaster
        if lr_prob <= self.low_conf_threshold:
            return {
                "prediction": 0,
                "confidence": float(1 - lr_prob),
                "source": "logistic_regression"
            }

        # Uncertain zone → fallback to Naive Bayes
        nb_prob = self.nb_model.predict_proba(X)[0][1]
        nb_pred = 1 if nb_prob >= 0.5 else 0

        return {
            "prediction": nb_pred,
            "confidence": float(nb_prob),
            "source": "naive_bayes_fallback"
        }