import pandas as pd
from preprocess import preprocess_data

df = pd.read_csv("/home/haider-cheema/Project_Ai_Prog/data/raw/train.csv")
print(f"Original data shape: {df.shape}")
print(f"\nOriginal columns: {list(df.columns)}")

X, y = preprocess_data(df)

print(f"\nPreprocessed X shape: {X.shape}")
print(f"Target y shape: {y.shape}")
print(f"\nFirst 5 rows of X:")
print(X.head())
print(f"\nFirst 5 values of y:")
print(y.head())
