from datetime import datetime, timezone
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from api import crud
from api.database import get_db, FirebaseDataConnectClient
from api.schemas import HealthResponse, PredictionResponse, TweetRequest
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
async def health_check(client: FirebaseDataConnectClient = Depends(get_db)) -> HealthResponse:
    model_loaded = False
    db_connected = False

    try:
        get_engine()
        model_loaded = True
    except Exception:
        logger.error("health.model_unavailable", exc_info=True)

    try:
        # Check if auth token generation succeeds as a proxy for client health
        # We don't have a simple SELECT 1 in Data Connect REST API
        await client.get_auth_token()
        db_connected = True
    except Exception:
        logger.error("health.database_unavailable", exc_info=True)

    status = "ok" if model_loaded and db_connected else "degraded"
    return HealthResponse(status=status, model_loaded=model_loaded, db_connected=db_connected)


@router.post("/predict", response_model=PredictionResponse)
async def predict_tweet(
    payload: TweetRequest,
    client: FirebaseDataConnectClient = Depends(get_db),
) -> PredictionResponse:
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
        # Run prediction in threadpool to prevent blocking the async event loop
        prediction = await run_in_threadpool(engine.predict, payload.text)
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
    event_timestamp = payload.event_timestamp or datetime.now(timezone.utc)

    try:
        request_row = await crud.create_request(client, payload)
        logger.info(
            "db.request_created",
            extra={"extra_data": {"request_id": request_row.id}},
        )

        prediction_row = await crud.create_prediction(
            client,
            request_id=request_row.id,
            disaster=bool(prediction["prediction"]),
            confidence=float(prediction["confidence"]),
            source=str(prediction["source"]),
        )
        logger.info(
            "db.prediction_created",
            extra={"extra_data": {"prediction_id": prediction_row.id, "request_id": request_row.id}},
        )
    except Exception as exc:
        logger.error("prediction.database_write_failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to persist prediction in database") from exc

    response = PredictionResponse(
        request_id=request_row.id,
        prediction_id=prediction_row.id,
        disaster=bool(prediction["prediction"]),
        confidence=round(float(prediction["confidence"]), 4),
        source=prediction["source"],
        event={
            "location": event_location,
            "timestamp": event_timestamp,
        },
    )

    logger.info(
        "prediction.completed",
        extra={
            "extra_data": {
                "request_id": request_row.id,
                "prediction_id": prediction_row.id,
                "disaster": response.disaster,
                "confidence": response.confidence,
                "source": response.source,
            }
        },
    )

    return response