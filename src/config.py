"""
config.py - Production Configuration
Centralized configuration for reproducibility and hyperparameters.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()

# Model Configuration
RANDOM_SEED = 42
TEST_SIZE = 0.2
LR_MAX_ITER = 1000

# Confidence Thresholds
HIGH_CONF_THRESHOLD = 0.75
LOW_CONF_THRESHOLD = 0.25

# Firebase Configuration
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "disaster-tweets-dev")
FIREBASE_CREDENTIALS_PATH = os.getenv(
	"FIREBASE_CREDENTIALS_PATH",
	"./secrets/firebase-key.json"
)

# Firestore Emulator (for local development)
# Set FIRESTORE_EMULATOR_HOST=localhost:8080 to use local emulator
FIRESTORE_EMULATOR_HOST = os.getenv("FIRESTORE_EMULATOR_HOST")
