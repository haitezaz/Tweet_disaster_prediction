from pydantic import BaseModel, Field


class TweetRequest(BaseModel):
	id: int | None = None
	keyword: str | None = None
	location: str | None = None
	text: str = Field(..., min_length=1, description="Tweet text used for prediction")
	target: int | None = None
	event_timestamp: str | None = None


class EventInfo(BaseModel):
	location: str
	timestamp: str


class PredictionResponse(BaseModel):
	disaster: bool
	confidence: float
	source: str
	event: EventInfo


class HealthResponse(BaseModel):
	status: str
	model_loaded: bool
