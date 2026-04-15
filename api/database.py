from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import DATABASE_URL, SQL_ECHO


is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
	DATABASE_URL,
	echo=SQL_ECHO,
	connect_args={"check_same_thread": False} if is_sqlite else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


def init_db() -> None:
	from api.models import Base

	Base.metadata.create_all(bind=engine)