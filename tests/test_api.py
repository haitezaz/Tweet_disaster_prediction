"""
test_api.py

End-to-end API tests for Assignment 3.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from api.main import app
from api.database import get_db

client = TestClient(app)

# Mock client to prevent actual network calls during tests
class MockFirebaseClient:
    async def get_auth_token(self):
        return "mock_token"

    async def execute_mutation(self, mutation_name, variables):
        if mutation_name == "CreateTweetRequest":
            return {"data": {"request_insert": {"id": "mock-uuid-1"}}}
        if mutation_name == "CreatePrediction":
            return {"data": {"prediction_insert": {"id": "mock-uuid-2"}}}
        return {}

    async def execute_query(self, query_name, variables):
        return {}

    async def close(self):
        pass

app.dependency_overrides[get_db] = lambda: MockFirebaseClient()

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

@patch("api.routes.get_engine")
def test_predict_valid_input(mock_get_engine):
    # Mock engine behavior
    mock_engine = MagicMock()
    mock_engine.predict.return_value = {
        "prediction": True,
        "confidence": 0.85,
        "source": "mock_source"
    }
    mock_get_engine.return_value = mock_engine

    payload = {
        "text": "Earthquake hits city causing damage"
    }

    # Mock DecisionEngine to avoid loading ML artifacts if missing in CI/CD,
    # or let it run if the models exist locally. They exist locally in 'artifacts/'
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

@patch("api.routes.get_engine")
def test_predict_long_text(mock_get_engine):
    mock_engine = MagicMock()
    mock_engine.predict.return_value = {
        "prediction": True,
        "confidence": 0.85,
        "source": "mock_source"
    }
    mock_get_engine.return_value = mock_engine

    payload = {
        "text": "fire " * 100  # very long input
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200


# ==============================
# WITH LOCATION & TIMESTAMP
# ==============================

@patch("api.routes.get_engine")
def test_predict_with_metadata(mock_get_engine):
    mock_engine = MagicMock()
    mock_engine.predict.return_value = {
        "prediction": True,
        "confidence": 0.85,
        "source": "mock_source"
    }
    mock_get_engine.return_value = mock_engine

    payload = {
        "text": "Flood reported in city",
        "location": "Lahore",
        "event_timestamp": "2026-03-30T12:00:00"
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["event"]["location"] == "Lahore"


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

@patch("api.routes.get_engine")
def test_performance(mock_get_engine):
    mock_engine = MagicMock()
    mock_engine.predict.return_value = {
        "prediction": True,
        "confidence": 0.85,
        "source": "mock_source"
    }
    mock_get_engine.return_value = mock_engine
    
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

    assert avg_latency < 1.0