from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
	pass


class Request(Base):
	__tablename__ = "requests"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	tweet_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
	text: Mapped[str] = mapped_column(Text, nullable=False)
	keyword: Mapped[str | None] = mapped_column(String(255), nullable=True)
	location: Mapped[str | None] = mapped_column(String(255), nullable=True)
	target: Mapped[int | None] = mapped_column(Integer, nullable=True)
	event_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=False),
		server_default=func.now(),
		nullable=False,
	)

	predictions: Mapped[list["Prediction"]] = relationship(
		"Prediction",
		back_populates="request",
		cascade="all, delete-orphan",
	)


class Prediction(Base):
	__tablename__ = "predictions"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"), nullable=False)
	disaster: Mapped[bool] = mapped_column(Boolean, nullable=False)
	confidence: Mapped[float] = mapped_column(Float, nullable=False)
	source: Mapped[str] = mapped_column(String(255), nullable=False)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=False),
		server_default=func.now(),
		nullable=False,
	)

	request: Mapped[Request] = relationship("Request", back_populates="predictions")