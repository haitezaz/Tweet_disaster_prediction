"""
Firestore Collections Reference
Document-oriented data models using Firestore.

Collections:
  - requests: Tweet input data
  - predictions: Model predictions with confidence scores
"""

# Collections reference
REQUESTS_COLLECTION = "requests"
PREDICTIONS_COLLECTION = "predictions"

# Request document structure
REQUEST_SCHEMA = {
	"tweet_id": "int | None",
	"text": "str",
	"keyword": "str | None",
	"location": "str | None",
	"target": "int | None",
	"event_timestamp": "datetime",
	"created_at": "datetime",
	"metadata": {
		"model_version": "str",
		"processing_time_ms": "int",
	},
}

# Prediction document structure
PREDICTION_SCHEMA = {
	"request_id": "str",
	"disaster": "bool",
	"confidence": "float",
	"source": "str",
	"created_at": "datetime",
	"model_metadata": {
		"model_version": "str",
	},
}