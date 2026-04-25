from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, HTMLResponse

from api import crud
from api.database import get_db, FirebaseDataConnectClient
from api.schemas import HealthResponse, PredictionResponse, TweetRequest
from src.models.decision_engine import DecisionEngine
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()
_API_DIR = Path(__file__).resolve().parent
_DASHBOARD_HTML = _API_DIR / "templates" / "dashboard.html"
_DASHBOARD_CSS = _API_DIR / "static" / "dashboard.css"
_DASHBOARD_JS = _API_DIR / "static" / "dashboard.js"


def _parse_timestamp(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return False


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bucket_floor(ts: datetime, bucket_minutes: int) -> datetime:
    minute_bucket = (ts.minute // bucket_minutes) * bucket_minutes
    return ts.replace(minute=minute_bucket, second=0, microsecond=0)


def _to_utc_z(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


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

@router.get("/data")
async def get_all_data(client: FirebaseDataConnectClient = Depends(get_db)):
    """Retrieve all data capped at 10,000 limit limit."""
    try:
        data = await crud.list_all_data(client)
        return data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page() -> FileResponse:
    return FileResponse(_DASHBOARD_HTML)


@router.get("/dashboard/assets/dashboard.css")
async def dashboard_css() -> FileResponse:
    return FileResponse(_DASHBOARD_CSS, media_type="text/css")


@router.get("/dashboard/assets/dashboard.js")
async def dashboard_js() -> FileResponse:
    return FileResponse(_DASHBOARD_JS, media_type="application/javascript")


@router.get("/dashboard/data")
async def dashboard_data(
    window_minutes: int = Query(default=60, ge=5, le=1440),
    bucket_minutes: int = Query(default=5, ge=1, le=60),
    recent_limit: int = Query(default=20, ge=5, le=100),
    client: FirebaseDataConnectClient = Depends(get_db),
) -> dict[str, Any]:
    try:
        data = await crud.list_all_data(client)
    except Exception as exc:
        logger.error("dashboard.data_fetch_failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard data") from exc

    requests_raw = data.get("requests", []) if isinstance(data, dict) else []
    predictions_raw = data.get("predictions", []) if isinstance(data, dict) else []

    if not isinstance(requests_raw, list):
        requests_raw = []
    if not isinstance(predictions_raw, list):
        predictions_raw = []

    request_map = {
        req.get("id"): req
        for req in requests_raw
        if isinstance(req, dict) and req.get("id")
    }

    now_utc = datetime.now(timezone.utc)
    window_start = now_utc - timedelta(minutes=window_minutes)

    true_count = 0
    false_count = 0
    confidence_sum = 0.0
    source_counts: dict[str, int] = defaultdict(int)
    bucket_counts: dict[datetime, dict[str, int]] = defaultdict(
        lambda: {"true": 0, "false": 0, "total": 0}
    )
    recent_items: list[dict[str, Any]] = []

    for pred in predictions_raw:
        if not isinstance(pred, dict):
            continue

        pred_ts = _parse_timestamp(pred.get("createdAt"))
        if pred_ts is None:
            continue
        if pred_ts < window_start or pred_ts > now_utc:
            continue

        request_id = pred.get("requestId")
        request_row = request_map.get(request_id, {})

        disaster = _to_bool(pred.get("disaster"))
        confidence = max(0.0, min(1.0, _to_float(pred.get("confidence"), 0.0)))
        source = str(pred.get("source") or "unknown")

        if disaster:
            true_count += 1
        else:
            false_count += 1

        confidence_sum += confidence
        source_counts[source] += 1

        bucket_ts = _bucket_floor(pred_ts, bucket_minutes)
        bucket_counts[bucket_ts]["total"] += 1
        if disaster:
            bucket_counts[bucket_ts]["true"] += 1
        else:
            bucket_counts[bucket_ts]["false"] += 1

        text = str(request_row.get("text") or "")
        recent_items.append(
            {
                "prediction_id": pred.get("id"),
                "request_id": request_id,
                "timestamp": _to_utc_z(pred_ts),
                "disaster": disaster,
                "confidence": round(confidence, 4),
                "source": source,
                "text": text,
                "text_preview": (text[:140] + "...") if len(text) > 140 else text,
                "location": request_row.get("location") or "Unknown",
            }
        )

    total = true_count + false_count
    true_rate = (true_count / total * 100.0) if total else 0.0
    avg_confidence = (confidence_sum / total) if total else 0.0

    series: list[dict[str, Any]] = []
    cursor = _bucket_floor(window_start, bucket_minutes)
    end_bucket = _bucket_floor(now_utc, bucket_minutes)
    while cursor <= end_bucket:
        bucket = bucket_counts.get(cursor, {"true": 0, "false": 0, "total": 0})
        series.append(
            {
                "timestamp": _to_utc_z(cursor),
                "label": cursor.strftime("%H:%M"),
                "true": bucket["true"],
                "false": bucket["false"],
                "total": bucket["total"],
            }
        )
        cursor += timedelta(minutes=bucket_minutes)

    recent_items.sort(key=lambda row: row.get("timestamp", ""), reverse=True)

    sources = [
        {"name": source, "count": count}
        for source, count in sorted(source_counts.items(), key=lambda item: item[1], reverse=True)
    ]

    return {
        "window_minutes": window_minutes,
        "bucket_minutes": bucket_minutes,
        "generated_at": _to_utc_z(now_utc),
        "summary": {
            "total": total,
            "true_count": true_count,
            "false_count": false_count,
            "true_rate": round(true_rate, 2),
            "avg_confidence": round(avg_confidence, 4),
        },
        "sources": sources,
        "series": series,
        "recent": recent_items[:recent_limit],
    }

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