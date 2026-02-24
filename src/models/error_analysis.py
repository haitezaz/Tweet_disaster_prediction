"""
error_analysis.py

Performs structured error analysis on classification results.

Responsibilities:
- Identify false positives
- Identify false negatives
- Print representative misclassified examples
- Support analytical reporting for Assignment 2
"""

import pandas as pd


def analyze_errors(model, X_val_tfidf, y_val, X_val_raw, num_samples=10):
    """
    Analyzes misclassified validation samples.

    Parameters:
    - model: trained classifier
    - X_val_tfidf: vectorized validation features
    - y_val: true labels
    - X_val_raw: original text validation samples
    - num_samples: number of examples to display
    """

    y_pred = model.predict(X_val_tfidf)

    results_df = pd.DataFrame({
        "text": X_val_raw.reset_index(drop=True),
        "true_label": y_val.reset_index(drop=True),
        "predicted_label": y_pred
    })

    # False Positives (Predicted Disaster but actually not)
    false_positives = results_df[
        (results_df["true_label"] == 0) &
        (results_df["predicted_label"] == 1)
    ]

    # False Negatives (Missed real disasters)
    false_negatives = results_df[
        (results_df["true_label"] == 1) &
        (results_df["predicted_label"] == 0)
    ]

    print("\n==============================")
    print("False Positives (Top Samples)")
    print("==============================")
    print(false_positives.head(num_samples))

    print("\n==============================")
    print("False Negatives (Top Samples)")
    print("==============================")
    print(false_negatives.head(num_samples))

    return {
        "false_positives": false_positives,
        "false_negatives": false_negatives
    }