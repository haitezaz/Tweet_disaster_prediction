from datetime import datetime
from functools import lru_cache

from fastapi import APIRouter, HTTPException

from api import crud
from api.firebase_db import get_firebase_db
from api.schemas import EventInfo, HealthResponse, PredictionResponse, TweetRequest
from src.models.decision_engine import DecisionEngine
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@lru_cache(maxsize=1)
def get_engine() -> DecisionEngine:
	logger.info(
		"model.engine_loading",
		extra={"extra_data": {"component": "decision_engine"}},
	)
	return DecisionEngine()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
	"""Health check endpoint"""
	model_loaded = False
	db_connected = False

	try:
		get_engine()
		model_loaded = True
	except Exception:
		logger.error("health.model_unavailable", exc_info=True)

	try:
		db = get_firebase_db()
		db_connected = db.health_check()
	except Exception:
		logger.error("health.database_unavailable", exc_info=True)

	status = "ok" if model_loaded and db_connected else "degraded"
	return HealthResponse(status=status, model_loaded=model_loaded, db_connected=db_connected)


@router.post("/predict", response_model=PredictionResponse)
def predict_tweet(payload: TweetRequest) -> PredictionResponse:
	"""
	Make disaster prediction on tweet.
	
	This endpoint:
	1. Receives tweet text
	2. Runs confidence-aware prediction models
	3. Stores request and prediction in Firestore
	4. Returns prediction with confidence score
	"""
	logger.info(
		"prediction.request_received",
		extra={
			"extra_data": {
				"input_text": payload.text,
				"location": payload.location,
				"timestamp": payload.event_timestamp.isoformat() if payload.event_timestamp else None,
			}
		},
	)

	try:
		engine = get_engine()
	except Exception as exc:
		logger.error("prediction.model_loading_failed", exc_info=True)
		raise HTTPException(status_code=503, detail=f"Model artifacts are unavailable: {exc}") from exc

	try:
		prediction = engine.predict(payload.text)
	except ValueError as exc:
		logger.warning(
			"prediction.invalid_input",
			extra={"extra_data": {"reason": str(exc), "input_text": payload.text}},
		)
		raise HTTPException(status_code=400, detail=str(exc)) from exc
	except Exception as exc:
		logger.error("prediction.model_failed", exc_info=True)
		raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

	if not {"prediction", "confidence", "source"}.issubset(prediction):
		logger.error(
			"prediction.invalid_output",
			extra={"extra_data": {"prediction_payload": prediction}},
		)
		raise HTTPException(status_code=500, detail="Model returned invalid output format")

	event_location = payload.location.strip() if payload.location and payload.location.strip() else "Unknown"
	event_timestamp = payload.event_timestamp or datetime.utcnow()

	try:
		# Create request document in Firestore
		request_doc = crud.create_request(payload)
		logger.info(
			"firestore.request_created",
			extra={"extra_data": {"request_id": request_doc.id}},
		)

		# Create prediction document in Firestore
		prediction_doc = crud.create_prediction(
			request_id=request_doc.id,
			disaster=bool(prediction["prediction"]),
			confidence=float(prediction["confidence"]),
			source=str(prediction["source"]),
		)
		logger.info(
			"firestore.prediction_created",
			extra={
				"extra_data": {
					"prediction_id": prediction_doc.id,
					"request_id": request_doc.id,
				}
			},
		)
	except Exception as exc:
		logger.error("prediction.database_write_failed", exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to persist prediction in database") from exc

	response = PredictionResponse(
		request_id=request_doc.id,
		prediction_id=prediction_doc.id,
		disaster=bool(prediction["prediction"]),
		confidence=round(float(prediction["confidence"]), 4),
		source=prediction["source"],
		event=EventInfo(
			location=event_location,
			timestamp=event_timestamp,
		),
	)

	logger.info(
		"prediction.completed",
		extra={
			"extra_data": {
				"request_id": request_doc.id,
				"prediction_id": prediction_doc.id,
				"disaster": response.disaster,
				"confidence": response.confidence,
				"source": response.source,
			}
		},
	)

	return response


@router.get("/history")
def get_history(limit: int = 10) -> list[dict]:
	"""Get recent prediction history"""
	try:
		requests = crud.get_recent_requests(limit=limit)
		
		result = []
		for req in requests:
			predictions = crud.get_predictions_for_request(req.id)
			result.append({
				"request_id": req.id,
				"text": req.text,
				"created_at": req.created_at.isoformat() if req.created_at else None,
				"predictions": [
					{
						"disaster": p.disaster,
						"confidence": p.confidence,
						"source": p.source,
					}
					for p in predictions
				],
			})
		
		return result
	except Exception as exc:
		logger.error("history.fetch_failed", exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to fetch history") from exc
        