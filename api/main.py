from fastapi import FastAPI

from api.database import init_db
from api.routes import router
from src.utils.logger import configure_logging, get_logger


configure_logging()
logger = get_logger(__name__)


app = FastAPI(
	title="Disaster Tweet Prediction API",
	version="2.0.0",
	description="Confidence-aware disaster tweet classifier with Firestore backend.",
)


@app.on_event("startup")
def on_startup() -> None:
	init_db()
	logger.info("firestore.initialized")


app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
	logger.info("api.root_called")
	return {"message": "Disaster Tweet Prediction API is running with Firestore backend"}
