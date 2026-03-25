from datetime import datetime
from functools import lru_cache

from fastapi import APIRouter, HTTPException

from api.schemas import HealthResponse, PredictionResponse, TweetRequest
from src.models.decision_engine import DecisionEngine

router = APIRouter()


@lru_cache(maxsize=1)
def get_engine() -> DecisionEngine:
	return DecisionEngine()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
	try:
		get_engine()
		return HealthResponse(status="ok", model_loaded=True)
	except Exception:
		return HealthResponse(status="degraded", model_loaded=False)


@router.post("/predict", response_model=PredictionResponse)
def predict_tweet(payload: TweetRequest) -> PredictionResponse:
	try:
		engine = get_engine()
	except Exception as exc:
		raise HTTPException(status_code=503, detail=f"Model artifacts are unavailable: {exc}") from exc

	try:
		prediction = engine.predict(payload.text)
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

	event_location = payload.location.strip() if payload.location and payload.location.strip() else "Unknown"
	event_timestamp = payload.event_timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	return PredictionResponse(
		disaster=bool(prediction["prediction"]),
		confidence=round(float(prediction["confidence"]), 4),
		source=prediction["source"],
		event={
			"location": event_location,
			"timestamp": event_timestamp,
		},
	)
