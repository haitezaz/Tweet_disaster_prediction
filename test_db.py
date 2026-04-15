"""
Firebase Database Connection Test
Verifies Firestore connectivity and basic operations.
"""

from api.database import init_db
from api.firebase_db import get_firebase_db
from api.schemas import TweetRequest
from api import crud
from src.config import FIREBASE_PROJECT_ID


def test() -> None:
	"""Test Firebase Firestore connection and basic CRUD operations"""
	
	print(f"Testing Firebase Project: {FIREBASE_PROJECT_ID}")
	
	# Initialize Firestore
	init_db()
	print("✓ Firestore initialized")
	
	# Get Firebase client
	db = get_firebase_db()
	print("✓ Firebase client obtained")
	
	# Health check
	if db.health_check():
		print("✓ Firestore health check passed")
	else:
		print("✗ Firestore health check failed")
		return
	
	# Test create_request
	print("\nTesting CRUD operations:")
	payload = TweetRequest(
		text="Test tweet for disaster prediction",
		keyword="test",
		location="Test Location"
	)
	
	try:
		request_doc = crud.create_request(payload)
		print(f"✓ Request created: {request_doc.id}")
	except Exception as exc:
		print(f"✗ Request creation failed: {exc}")
		return
	
	# Test create_prediction
	try:
		pred_doc = crud.create_prediction(
			request_id=request_doc.id,
			disaster=True,
			confidence=0.87,
			source="test_model"
		)
		print(f"✓ Prediction created: {pred_doc.id}")
	except Exception as exc:
		print(f"✗ Prediction creation failed: {exc}")
		return
	
	# Test get_request
	try:
		retrieved_request = crud.get_request(request_doc.id)
		if retrieved_request:
			print(f"✓ Request retrieved: {retrieved_request.text[:50]}...")
		else:
			print("✗ Request not found")
	except Exception as exc:
		print(f"✗ Request retrieval failed: {exc}")
		return
	
	# Test get_predictions_for_request
	try:
		predictions = crud.get_predictions_for_request(request_doc.id)
		print(f"✓ Predictions retrieved: {len(predictions)} prediction(s)")
	except Exception as exc:
		print(f"✗ Predictions retrieval failed: {exc}")
		return
	
	print("\n✓ All Firestore tests passed!")


if __name__ == "__main__":
	test()