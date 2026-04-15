from __future__ import annotations

from sqlalchemy.orm import Session

from api.models import Prediction, Request
from api.schemas import TweetRequest


def create_request(session: Session, payload: TweetRequest) -> Request:
	request_row = Request(
		tweet_id=payload.tweet_id,
		text=payload.text,
		keyword=payload.keyword,
		location=payload.location,
		target=payload.target,
		event_timestamp=payload.event_timestamp,
	)
	try:
		session.add(request_row)
		session.commit()
		session.refresh(request_row)
	except Exception:
		session.rollback()
		raise
	return request_row


def create_prediction(
	session: Session,
	*,
	request_id: int,
	disaster: bool,
	confidence: float,
	source: str,
) -> Prediction:
	prediction_row = Prediction(
		request_id=request_id,
		disaster=disaster,
		confidence=confidence,
		source=source,
	)
	try:
		session.add(prediction_row)
		session.commit()
		session.refresh(prediction_row)
	except Exception:
		session.rollback()
		raise
	return prediction_row