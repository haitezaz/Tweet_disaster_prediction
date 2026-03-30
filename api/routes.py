from datetime import datetime
from functools import lru_cache
import logging

from fastapi import APIRouter, HTTPException

from api.schemas import HealthResponse, PredictionResponse, TweetRequest
from src.models.decision_engine import DecisionEngine

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@lru_cache(maxsize=1)
def get_engine() -> DecisionEngine:
    logger.info("Loading Decision Engine...")
    return DecisionEngine()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    try:
        get_engine()
        logger.info("Health check passed: model loaded successfully")
        return HealthResponse(status="ok", model_loaded=True)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(status=f"degraded: {str(e)}", model_loaded=False)


@router.post("/predict", response_model=PredictionResponse)
def predict_tweet(payload: TweetRequest) -> PredictionResponse:
    logger.info(f"Received prediction request | text={payload.text[:50]}...")

    try:
        engine = get_engine()
    except Exception as exc:
        logger.error(f"Model loading failed: {exc}")
        raise HTTPException(status_code=503, detail=f"Model artifacts are unavailable: {exc}") from exc

    try:
        prediction = engine.predict(payload.text)
        logger.info(f"Model prediction: {prediction}")
    except ValueError as exc:
        logger.warning(f"Invalid input: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Prediction failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

    event_location = payload.location.strip() if payload.location and payload.location.strip() else "Unknown"
    event_timestamp = payload.event_timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    response = PredictionResponse(
        disaster=bool(prediction["prediction"]),
        confidence=round(float(prediction["confidence"]), 4),
        source=prediction["source"],
        event={
            "location": event_location,
            "timestamp": event_timestamp,
        },
    )

    logger.info(f"Response sent: {response}")

    return response