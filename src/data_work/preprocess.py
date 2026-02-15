"""
preprocess.py

Handles all data preprocessing steps required before model training
or inference. This includes cleaning, encoding, and scaling operations.

Responsibilities:
- Handle missing values
- Encode categorical variables
- Scale or normalize numerical features
- Separate features (X) and target variable (y)

This module ensures that preprocessing logic is reusable and
consistent across training and inference stages.
"""
import pandas as pd
import re


def clean_text(text):
    """
    Performs basic text normalization.
    This function intentionally avoids aggressive NLP processing.
    
    Args:
        text (str): Raw text to clean
        
    Returns:
        str: Cleaned text
    """
    if not isinstance(text, str):
        return ""
    
    text = text.lower()                      # lowercase
    text = re.sub(r"http\S+", "", text)      # remove URLs
    text = re.sub(r"@\w+", "", text)         # remove mentions
    text = re.sub(r"#", "", text)            # remove hashtag symbol
    text = re.sub(r"[^a-z\s]", "", text)     # remove punctuation & numbers
    text = re.sub(r"\s+", " ", text).strip() # normalize spaces
    
    return text


def preprocess_data(df, target_col="target"):
    """
    Preprocessing pipeline for Assignment 1.
    Handles column selection and basic text cleaning.
    
    Args:
        df (pd.DataFrame): Raw dataframe
        target_col (str): Name of target column
        
    Returns:
        tuple: (X, y) where X is features and y is target
        
    Raises:
        ValueError: If required columns are missing
    """
    # Validate input
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")
    
    if "text" not in df.columns:
        raise ValueError("DataFrame must contain 'text' column")
    
    # Check if this is training data (has target) or test data
    has_target = target_col in df.columns
    
    # Drop non-informative or noisy columns
    cols_to_drop = ["id", "keyword", "location"]
    df = df.drop(columns=cols_to_drop, errors="ignore")
    
    # Handle missing values in text column
    if df["text"].isnull().any():
        print(f"⚠ Warning: Found {df['text'].isnull().sum()} missing text values. Filling with empty string.")
        df["text"] = df["text"].fillna("")

    # Clean text column
    print("Cleaning text data...")
    df["text"] = df["text"].apply(clean_text)
    
    # Remove empty texts after cleaning
    empty_texts = (df["text"] == "")
    if empty_texts.any():
        print(f"⚠ Warning: {empty_texts.sum()} texts are empty after cleaning. Removing them.")
        df = df[~empty_texts].reset_index(drop=True)

    # Separate features and target
    X = df["text"]
    
    if has_target:
        y = df[target_col]
        return X, y
    else:
        return X