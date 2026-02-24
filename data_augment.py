"""
augment_dataset.py

Creates an extended version of the disaster tweets dataset
by adding synthetic location and timestamp metadata.

IMPORTANT:
- Original dataset remains unchanged.
- New metadata is NOT used for model training.
- This extension is created solely for product-level system design.
"""

import pandas as pd
import random
from datetime import datetime, timedelta


# 50 predefined global cities
LOCATIONS = [
    "Lahore", "Karachi", "Islamabad", "Peshawar", "Quetta",
    "New York", "London", "Tokyo", "Delhi", "Sydney",
    "Toronto", "Dubai", "Paris", "Berlin", "Rome",
    "Madrid", "Beijing", "Moscow", "Bangkok", "Istanbul",
    "Cairo", "Seoul", "Singapore", "Kuala Lumpur", "Jakarta",
    "Los Angeles", "Chicago", "Houston", "Miami", "Boston",
    "San Francisco", "Vancouver", "Melbourne", "Auckland", "Doha",
    "Riyadh", "Tehran", "Baghdad", "Nairobi", "Cape Town",
    "Mexico City", "Sao Paulo", "Buenos Aires", "Lima", "Santiago",
    "Athens", "Warsaw", "Stockholm", "Helsinki", "Oslo"
]


def generate_random_timestamp():
    """
    Generates a random timestamp within the last 60 days.
    """
    now = datetime.now()
    random_days = random.randint(0, 60)
    random_seconds = random.randint(0, 86400)

    random_time = now - timedelta(days=random_days, seconds=random_seconds)
    return random_time.strftime("%Y-%m-%d %H:%M:%S")


def augment_dataset(input_path: str, output_path: str):
    df = pd.read_csv("/home/haider-cheema/Project_Ai_Prog/Tweet_disaster_prediction/data/raw/train.csv")

    # Set fixed seed for reproducibility
    random.seed(42)


    df["event_timestamp"] = [generate_random_timestamp() for _ in range(len(df))]

    df.to_csv("/home/haider-cheema/Project_Ai_Prog/Tweet_disaster_prediction/data/raw/mod_train.csv", index=False)

    print(f"Extended dataset saved to: {output_path}")
    print(f"New shape: {df.shape}")
    print("New columns added: event_location, event_timestamp")


if __name__ == "__main__":
    augment_dataset(
        input_path="data/raw/train.csv",
        output_path="data/raw/extended_train.csv"
    )