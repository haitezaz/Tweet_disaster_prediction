"""
config.py

Central configuration file for reproducibility and hyperparameters.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()

RANDOM_SEED = 42

TEST_SIZE = 0.2

LR_MAX_ITER = 1000

HIGH_CONF_THRESHOLD = 0.75
LOW_CONF_THRESHOLD = 0.25

# Firebase Data Connect Configuration
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "tweet-disaster-prediction")
FIREBASE_LOCATION = os.getenv("FIREBASE_LOCATION", "us-east4")
DATA_CONNECT_SERVICE_ID = os.getenv("DATA_CONNECT_SERVICE_ID", "tweetdisasterprediction")
DATA_CONNECT_CONNECTOR_ID = os.getenv("DATA_CONNECT_CONNECTOR_ID", "example")

# The path to your service account key file. Leave blank in .env and it won't be used
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
