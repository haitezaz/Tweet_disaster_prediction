"""
load_data.py

Responsible for loading raw datasets from disk into memory.
This module isolates data ingestion logic to ensure separation
between data access and data processing.

Responsibilities:
- Read raw data files (CSV or similar formats)
- Perform basic validation (file existence, schema sanity)
- Return data in a standardized pandas DataFrame format

No preprocessing, cleaning, or feature transformations are
performed in this module.
"""


import pandas as pd
import os
from pathlib import Path

# Define base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / 'data' / 'raw'

# Define file paths
TRAIN_FILE = DATA_DIR / 'train.csv'
TEST_FILE = DATA_DIR / 'test.csv'
SAMPLE_SUBMISSION_FILE = DATA_DIR / 'sample_submission.csv'


def load_train_data():
    """
    Load the training dataset from disk.
    
    Returns:
        pd.DataFrame: Training data as a pandas DataFrame
        
    Raises:
        FileNotFoundError: If the train.csv file does not exist
    """
    if not TRAIN_FILE.exists():
        raise FileNotFoundError(f"Training file not found at: {TRAIN_FILE}")
    
    df = pd.read_csv(TRAIN_FILE)
    print(f"✓ Loaded training data: {df.shape[0]} rows, {df.shape[1]} columns")
    return df


def load_test_data():
    """
    Load the test dataset from disk.
    
    Returns:
        pd.DataFrame: Test data as a pandas DataFrame
        
    Raises:
        FileNotFoundError: If the test.csv file does not exist
    """
    if not TEST_FILE.exists():
        raise FileNotFoundError(f"Test file not found at: {TEST_FILE}")
    
    df = pd.read_csv(TEST_FILE)
    print(f"✓ Loaded test data: {df.shape[0]} rows, {df.shape[1]} columns")
    return df





def load_data(file_path):
    """
    Generic function to load any CSV file.
    
    Args:
        file_path (str or Path): Path to the CSV file
        
    Returns:
        pd.DataFrame: Data as a pandas DataFrame
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found at: {file_path}")
    
    df = pd.read_csv(file_path)
    print(f"✓ Loaded data from {file_path.name}: {df.shape[0]} rows, {df.shape[1]} columns")
    return df


if __name__ == "__main__":
    # Test data loading functions
    print("Testing data loading functions...\n")
    
    try:
        train_df = load_train_data()
        print(f"Train columns: {list(train_df.columns)}\n")
    except FileNotFoundError as e:
        print(f"Error: {e}\n")
    
    try:
        test_df = load_test_data()
        print(f"Test columns: {list(test_df.columns)}\n")
    except FileNotFoundError as e:
        print(f"Error: {e}\n")
    

