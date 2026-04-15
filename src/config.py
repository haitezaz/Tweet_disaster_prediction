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

# Database configuration (forced to local SQLite for stable development)
DATABASE_URL = "sqlite:///./test.db"
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"
