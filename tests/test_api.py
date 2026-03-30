"""
test_api.py

End-to-end API tests for Assignment 3.

Covers:
- Health endpoint
- Prediction endpoint (valid input)
- Input validation
- Edge cases
- Error handling
- Basic performance sanity
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


# ==============================
# HEALTH CHECK
# ==============================

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "model_loaded" in data


# ==============================
# VALID PREDICTION
# ==============================

def test_predict_valid_input():
    payload = {
        "text": "Earthquake hits city causing damage"
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert "disaster" in data
    assert "confidence" in data
    assert "source" in data
    assert "event" in data

    assert isinstance(data["disaster"], bool)
    assert isinstance(data["confidence"], float)


# ==============================
# EMPTY TEXT (SHOULD FAIL)
# ==============================

def test_predict_empty_text():
    payload = {
        "text": ""
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 422  # validation error


# ==============================
# MISSING TEXT FIELD
# ==============================

def test_predict_missing_text():
    payload = {}

    response = client.post("/predict", json=payload)

    assert response.status_code == 422


# ==============================
# LONG TEXT (EDGE CASE)
# ==============================

def test_predict_long_text():
    payload = {
        "text": "fire " * 100  # very long input
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200


# ==============================
# WITH LOCATION & TIMESTAMP
# ==============================

def test_predict_with_metadata():
    payload = {
        "text": "Flood reported in city",
        "location": "Lahore",
        "event_timestamp": "2026-03-30 12:00:00"
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["event"]["location"] == "Lahore"
    assert data["event"]["timestamp"] == "2026-03-30 12:00:00"


# ==============================
# INVALID DATA TYPE
# ==============================

def test_invalid_data_type():
    payload = {
        "text": 12345  # invalid type
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 422


# ==============================
# BASIC PERFORMANCE TEST
# ==============================

def test_performance():
    import time

    payload = {
        "text": "Earthquake hits downtown area"
    }

    num_requests = 20
    start_time = time.time()

    for _ in range(num_requests):
        response = client.post("/predict", json=payload)
        assert response.status_code == 200

    total_time = time.time() - start_time
    avg_latency = total_time / num_requests

    print(f"\nTotal time: {total_time:.4f}s")
    print(f"Average latency: {avg_latency:.4f}s")

    # sanity check (not strict)
    assert avg_latency < 1.0