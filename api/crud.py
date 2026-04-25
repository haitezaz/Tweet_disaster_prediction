from __future__ import annotations

import datetime
from datetime import datetime as dt, timezone
from dataclasses import dataclass
from api.database import FirebaseDataConnectClient
from api.schemas import TweetRequest


@dataclass
class RequestRow:
    id: str

@dataclass
class PredictionRow:
    id: str


async def create_request(client: FirebaseDataConnectClient, payload: TweetRequest) -> RequestRow:
    variables = {
        "text": payload.text,
        "keyword": payload.keyword,
        "location": payload.location,
        "target": payload.target,
        "eventTimestamp": payload.event_timestamp.isoformat().replace("+00:00", "Z") if payload.event_timestamp else None,
        "createdAt": dt.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    try:
        response = await client.execute_mutation("CreateTweetRequest", variables)
        data = response.get("data", {})
        inserted = data.get("request_insert", {})
        if isinstance(inserted, dict):
            request_id = inserted.get("id", "")
        else:
            request_id = str(inserted) if inserted else ""
        return RequestRow(id=request_id)
    except Exception as exc:
        print(f"Error creating request: {exc}")
        raise


async def create_prediction(
    client: FirebaseDataConnectClient,
    *,
    request_id: str,
    disaster: bool,
    confidence: float,
    source: str,
) -> PredictionRow:
    variables = {
        "requestId": request_id,
        "disaster": disaster,
        "confidence": confidence,
        "source": source,
        "createdAt": dt.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    try:
        response = await client.execute_mutation("CreatePrediction", variables)
        data = response.get("data", {})
        inserted = data.get("prediction_insert", {})
        if isinstance(inserted, dict):
            prediction_id = inserted.get("id", "")
        else:
            prediction_id = str(inserted) if inserted else ""
        return PredictionRow(id=prediction_id)
    except Exception as exc:
        print(f"Error creating prediction: {exc}")
        raise

async def list_all_data(client: FirebaseDataConnectClient) -> dict:
    try:
        response = await client.execute_query("ListAllData", {})
        return response.get("data", {})
    except Exception as exc:
        print(f"Error fetching data: {exc}")
        raise