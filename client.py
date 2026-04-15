#!/usr/bin/env python3
"""
Real-time API client for testing the Tweet Disaster Prediction API.
Tests health check and prediction endpoints.
"""

import json
from datetime import datetime, timezone

import requests

API_BASE_URL = "http://127.0.0.1:8000"


def print_header(title: str) -> None:
	"""Print a formatted section header."""
	print(f"\n{'=' * 60}")
	print(f"  {title}")
	print(f"{'=' * 60}\n")


def test_health() -> bool:
	"""Test the health check endpoint."""
	print_header("HEALTH CHECK")
	
	try:
		response = requests.get(f"{API_BASE_URL}/health", timeout=30)
		response.raise_for_status()
		data = response.json()
		
		print("✓ Health check successful!")
		print(f"  Status: {data.get('status')}")
		print(f"  Model Loaded: {data.get('model_loaded')}")
		print(f"  DB Connected: {data.get('db_connected')}")
		
		return data.get('status') == 'ok'
	except (requests.RequestException, json.JSONDecodeError) as e:
		print(f"✗ Health check failed: {e}")
		return False


def test_prediction(text: str, location: str = "Unknown") -> dict | None:
	"""Test the prediction endpoint."""
	print_header("PREDICTION TEST")
	
	payload = {
		"text": text,
		"location": location,
		"event_timestamp": datetime.now(timezone.utc).isoformat(),
	}
	
	print(f"Request Payload:")
	print(json.dumps(payload, indent=2, default=str))
	
	try:
		response = requests.post(
			f"{API_BASE_URL}/predict",
			json=payload,
			timeout=60,
		)
		response.raise_for_status()
		data = response.json()
		
		print(f"\n✓ Prediction successful!")
		print(f"\nResponse:")
		print(json.dumps(data, indent=2, default=str))
		
		return data
	except requests.exceptions.ConnectionError:
		print("✗ Connection failed. Is the API server running? (uvicorn api.main:app --reload)")
		return None
	except (requests.RequestException, json.JSONDecodeError) as e:
		print(f"✗ Prediction failed: {e}")
		if hasattr(e, 'response') and e.response is not None:
			try:
				error_data = e.response.json()
				print(f"Error details: {json.dumps(error_data, indent=2)}")
			except json.JSONDecodeError:
				print(f"Response text: {e.response.text}")
		return None


def test_history() -> list[dict] | None:
	"""Test the history endpoint."""
	print_header("HISTORY TEST")
	
	try:
		response = requests.get(
			f"{API_BASE_URL}/history?limit=5",
			timeout=30,
		)
		response.raise_for_status()
		data = response.json()
		
		print(f"✓ History fetch successful!")
		print(f"  Found {len(data)} recent predictions")
		
		if data:
			print(f"\nLatest predictions:")
			print(json.dumps(data[:2], indent=2, default=str))
		
		return data
	except (requests.RequestException, json.JSONDecodeError) as e:
		print(f"✗ History fetch failed: {e}")
		return None


def main():
	"""Run all tests."""
	print("\n" + "=" * 60)
	print("  TWEET DISASTER PREDICTION API - CLIENT TEST")
	print("=" * 60)
	print(f"  API URL: {API_BASE_URL}")
	print(f"  Time: {datetime.now().isoformat()}")
	
	# Test 1: Health check
	health_ok = test_health()
	
	if not health_ok:
		print("\n⚠️  API health check failed. Continuing with prediction test anyway...")
	
	# Test 2: Make predictions
	test_samples = [
		"Just got a disaster alert! The earthquake hit near the coast.",
		"Weather is beautiful today, going for a walk in the park",
		"Flood warning issued for the downtown area - evacuate immediately!",
	]
	
	predictions = []
	for sample_text in test_samples:
		result = test_prediction(sample_text, location="Sample City")
		if result:
			predictions.append(result)
	
	# Test 3: Get history
	if predictions:
		test_history()
	
	# Summary
	print_header("TEST SUMMARY")
	print(f"✓ Total predictions tested: {len(predictions)}")
	print(f"✓ Disaster predictions: {sum(1 for p in predictions if p.get('disaster'))}")
	print(f"✓ Non-disaster predictions: {sum(1 for p in predictions if not p.get('disaster'))}")
	
	if predictions:
		avg_confidence = sum(p.get('confidence', 0) for p in predictions) / len(predictions)
		print(f"✓ Average confidence: {avg_confidence:.4f}")
	
	print("\n✅ All tests completed!\n")


if __name__ == "__main__":
	main()
