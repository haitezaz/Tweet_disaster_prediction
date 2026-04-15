from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from api.database import SessionLocal, init_db
from src.config import DATABASE_URL


def test() -> None:
	print(f"Testing DB URL: {DATABASE_URL}")
	init_db()

	db = SessionLocal()
	try:
		result = db.execute(text("SELECT 1"))
		print("Connected successfully!")
		print(f"Health query result: {result.scalar_one()}")
	except SQLAlchemyError as exc:
		print("SQLAlchemy database error:")
		print(str(exc))
		raise
	finally:
		db.close()


if __name__ == "__main__":
	test()