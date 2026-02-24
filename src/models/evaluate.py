"""
evaluate.py

Provides evaluation utilities for trained classification models.
This module computes multiple metrics required for Assignment 2.

Responsibilities:
- Compute classification metrics
- Generate confusion matrix
- Print structured evaluation summary
"""

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


def evaluate_model(model, X_val, y_val):
    """
    Evaluates a trained model on validation data.
    Returns a dictionary of metrics.
    """

    y_pred = model.predict(X_val)

    metrics = {
        "accuracy": accuracy_score(y_val, y_pred),
        "precision": precision_score(y_val, y_pred),
        "recall": recall_score(y_val, y_pred),
        "f1_score": f1_score(y_val, y_pred),
        "confusion_matrix": confusion_matrix(y_val, y_pred)
    }

    print("\n=== Evaluation Metrics ===")
    print(f"Accuracy  : {metrics['accuracy']:.4f}")
    print(f"Precision : {metrics['precision']:.4f}")
    print(f"Recall    : {metrics['recall']:.4f}")
    print(f"F1-Score  : {metrics['f1_score']:.4f}")

    print("\n=== Confusion Matrix ===")
    print(metrics["confusion_matrix"])

    print("\n=== Classification Report ===")
    print(classification_report(y_val, y_pred))

    return metrics