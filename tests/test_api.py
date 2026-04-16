"""
test_api.py

End-to-end API tests for Assignment 3 (Async Version).

Covers:
- Health endpoint
- Prediction endpoint (valid input)
- Input validation
- Edge cases
- Error handling
- Basic performance sanity
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from api.main import app


@pytest_asyncio.fixture
async def client():
	"""Async client fixture for testing"""
	async with AsyncClient(app=app, base_url="http://test") as async_client:
		yield async_client


# ==============================
# HEALTH CHECK
# ==============================

@pytest.mark.asyncio
async def test_health_endpoint(client):
	"""Test health check endpoint"""
	response = await client.get("/health")
	assert response.status_code == 200
	data = response.json()

	assert "status" in data
	assert "model_loaded" in data


# ==============================
# VALID PREDICTION
# ==============================

@pytest.mark.asyncio
async def test_predict_valid_input(client):
	"""Test prediction with valid input"""
	payload = {
		"text": "Earthquake hits city causing damage"
	}

	response = await client.post("/predict", json=payload)

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

@pytest.mark.asyncio
async def test_predict_empty_text(client):
	"""Test prediction with empty text - should fail validation"""
	payload = {
		"text": ""
	}

	response = await client.post("/predict", json=payload)

	assert response.status_code == 422  # validation error


# ==============================
# MISSING TEXT FIELD
# ==============================

@pytest.mark.asyncio
async def test_predict_missing_text(client):
	"""Test prediction with missing text field - should fail validation"""
	payload = {}

	response = await client.post("/predict", json=payload)

	assert response.status_code == 422


# ==============================
# LONG TEXT (EDGE CASE)
# ==============================

@pytest.mark.asyncio
async def test_predict_long_text(client):
	"""Test prediction with very long text"""
	payload = {
		"text": "fire " * 100  # very long input
	}

	response = await client.post("/predict", json=payload)

	assert response.status_code == 200


# ==============================
# WITH LOCATION & TIMESTAMP
# ==============================

@pytest.mark.asyncio
async def test_predict_with_metadata(client):
	"""Test prediction with location and timestamp metadata"""
	payload = {
		"text": "Flood reported in city",
		"location": "Lahore",
		"event_timestamp": "2026-03-30T12:00:00"
	}

	response = await client.post("/predict", json=payload)

	assert response.status_code == 200

	data = response.json()

	assert data["event"]["location"] == "Lahore"


# ==============================
# INVALID DATA TYPE
# ==============================

@pytest.mark.asyncio
async def test_invalid_data_type(client):
	"""Test prediction with invalid data type - should fail validation"""
	payload = {
		"text": 12345  # invalid type
	}

	response = await client.post("/predict", json=payload)

	assert response.status_code == 422


# ==============================
# HISTORY ENDPOINT
# ==============================

@pytest.mark.asyncio
async def test_history_endpoint(client):
	"""Test history endpoint"""
	response = await client.get("/history?limit=5")
	assert response.status_code == 200
	
	data = response.json()
	assert isinstance(data, list)


# ==============================
# ROOT ENDPOINT
# ==============================

@pytest.mark.asyncio
async def test_root_endpoint(client):
	"""Test root endpoint"""
	response = await client.get("/")
	assert response.status_code == 200
	
	data = response.json()
	assert "message" in data
	assert data["message"] == "API running"