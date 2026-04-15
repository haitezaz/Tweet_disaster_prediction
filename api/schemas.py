from __future__ import annotations

from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_serializer, field_validator


class TweetRequest(BaseModel):
	model_config = ConfigDict(populate_by_name=True)

	tweet_id: int | None = Field(default=None, validation_alias=AliasChoices("tweet_id", "id"))
	keyword: str | None = None
	location: str | None = None
	text: str = Field(..., min_length=1, description="Tweet text used for prediction")
	target: int | None = Field(default=None, ge=0, le=1)
	event_timestamp: datetime | None = None

	@field_validator("text")
	@classmethod
	def validate_text(cls, value: str) -> str:
		cleaned = value.strip()
		if not cleaned:
			raise ValueError("text must not be empty or whitespace")
		return cleaned

	@field_validator("keyword", "location")
	@classmethod
	def normalize_optional_strings(cls, value: str | None) -> str | None:
		if value is None:
			return None
		cleaned = value.strip()
		return cleaned or None


class EventInfo(BaseModel):
	location: str
	timestamp: datetime

	@field_serializer("timestamp")
	def serialize_timestamp(self, value: datetime) -> str:
		return value.strftime("%Y-%m-%d %H:%M:%S")


class PredictionResponse(BaseModel):
	request_id: int
	prediction_id: int
	disaster: bool
	confidence: float
	source: str
	event: EventInfo


class HealthResponse(BaseModel):
	status: str
	model_loaded: bool
	db_connected: bool
