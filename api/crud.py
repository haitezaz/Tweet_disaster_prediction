"""
Firestore CRUD Operations
Production-grade CRUD layer for Disaster Tweet Prediction system.
"""

from __future__ import annotations

from datetime import datetime, timezone

from api.firebase_db import get_firebase_db
from api.schemas import TweetRequest
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RequestDocument:
	"""Request document wrapper"""

	def __init__(self, data: dict):
		self.id: str = data.get("id", "")
		self.tweet_id: str | None = data.get("tweet_id")
		self.text: str = data.get("text", "")
		self.keyword: str | None = data.get("keyword")
		self.location: str | None = data.get("location")
		self.target: int | None = data.get("target")
		self.event_timestamp: datetime | None = data.get("event_timestamp")
		self.created_at: datetime | None = data.get("created_at")
		self.metadata: dict = data.get("metadata", {})


class PredictionDocument:
	"""Prediction document wrapper"""

	def __init__(self, data: dict):
		self.id: str = data.get("id", "")
		self.request_id: str = data.get("request_id", "")
		self.disaster: bool = data.get("disaster", False)
		self.confidence: float = data.get("confidence", 0.0)
		self.source: str = data.get("source", "")
		self.created_at: datetime | None = data.get("created_at")
		self.model_metadata: dict = data.get("model_metadata", {})


def create_request(payload: TweetRequest) -> RequestDocument:
	"""
	Create request document in Firestore.
	
	Args:
		payload: TweetRequest with tweet data
		
	Returns:
		RequestDocument with generated ID
	"""
	db = get_firebase_db()
	now = datetime.now(timezone.utc)

	data = {
		"tweet_id": payload.tweet_id,
		"text": payload.text,
		"keyword": payload.keyword,
		"location": payload.location,
		"target": payload.target,
		"event_timestamp": payload.event_timestamp or now,
		"created_at": now,
		"metadata": {
			"model_version": "1.0",
			"processing_time_ms": 0,
		},
	}

	try:
		request_id = db.create_document("requests", data)
		logger.info(
			"firestore.request_created",
			extra={"extra_data": {"request_id": request_id}},
		)
		return RequestDocument({"id": request_id, **data})
	except Exception as exc:
		logger.error("firestore.request_creation_failed", exc_info=True)
		raise


def get_request(request_id: str) -> RequestDocument | None:
	"""
	Get request by ID.
	
	Args:
		request_id: Request document ID
		
	Returns:
		RequestDocument or None if not found
	"""
	db = get_firebase_db()

	try:
		data = db.get_document("requests", request_id)
		if data:
			return RequestDocument({"id": request_id, **data})
		return None
	except Exception as exc:
		logger.error(
			"firestore.request_get_failed",
			extra={"extra_data": {"request_id": request_id}},
			exc_info=True,
		)
		raise


def get_recent_requests(limit: int = 10) -> list[RequestDocument]:
	"""
	Get recent requests.
	
	Args:
		limit: Max documents to return
		
	Returns:
		List of RequestDocument
	"""
	db = get_firebase_db()

	try:
		docs = db.query_collection(
			"requests",
			order_by=("created_at", "DESCENDING"),
			limit=limit,
		)
		return [RequestDocument(doc) for doc in docs]
	except Exception as exc:
		logger.error("firestore.requests_query_failed", exc_info=True)
		return []


def create_prediction(
	request_id: str,
	disaster: bool,
	confidence: float,
	source: str,
	model_metadata: dict | None = None,
) -> PredictionDocument:
	"""
	Create prediction document in Firestore.
	
	Args:
		request_id: Parent request ID
		disaster: Prediction result (True/False)
		confidence: Confidence score [0.0, 1.0]
		source: Model source (model_a, model_b, consensus)
		model_metadata: Optional model metadata
		
	Returns:
		PredictionDocument with generated ID
	"""
	db = get_firebase_db()
	now = datetime.now(timezone.utc)

	data = {
		"request_id": request_id,
		"disaster": disaster,
		"confidence": confidence,
		"source": source,
		"created_at": now,
		"model_metadata": model_metadata or {"model_version": "1.0"},
	}

	try:
		prediction_id = db.create_document("predictions", data)
		logger.info(
			"firestore.prediction_created",
			extra={
				"extra_data": {
					"prediction_id": prediction_id,
					"request_id": request_id,
				}
			},
		)
		return PredictionDocument({"id": prediction_id, **data})
	except Exception as exc:
		logger.error(
			"firestore.prediction_creation_failed",
			extra={"extra_data": {"request_id": request_id}},
			exc_info=True,
		)
		raise


def get_predictions_for_request(request_id: str) -> list[PredictionDocument]:
	"""
	Get all predictions for a request, ordered by newest first.
	Note: Uses in-memory sorting while Firestore composite index builds.
	Once index is READY, will use: request_id (ASC) + created_at (DESC)
	
	Args:
		request_id: Request document ID
		
	Returns:
		List of PredictionDocument (sorted by created_at descending)
	"""
	db = get_firebase_db()

	try:
		filters = [("request_id", "==", request_id)]
		docs = db.query_collection(
			"predictions",
			filters=filters,  # No ordering yet - index still building
		)
		# Sort in memory temporarily while index builds
		predictions = [PredictionDocument(doc) for doc in docs]
		predictions.sort(
			key=lambda p: p.created_at if p.created_at else datetime.now(timezone.utc),
			reverse=True
		)
		return predictions
	except Exception as exc:
		logger.error(
			"firestore.predictions_query_failed",
			extra={"extra_data": {"request_id": request_id}},
			exc_info=True,
		)
		return []


def get_prediction(prediction_id: str) -> PredictionDocument | None:
	"""
	Get prediction by ID.
	
	Args:
		prediction_id: Prediction document ID
		
	Returns:
		PredictionDocument or None if not found
	"""
	db = get_firebase_db()

	try:
		data = db.get_document("predictions", prediction_id)
		if data:
			return PredictionDocument({"id": prediction_id, **data})
		return None
	except Exception as exc:
		logger.error(
			"firestore.prediction_get_failed",
			extra={"extra_data": {"prediction_id": prediction_id}},
			exc_info=True,
		)
		raise