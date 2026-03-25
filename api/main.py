from fastapi import FastAPI

from api.routes import router


app = FastAPI(
	title="Disaster Tweet Prediction API",
	version="1.0.0",
	description="Confidence-aware disaster tweet classifier with structured event output.",
)

app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
	return {"message": "Disaster Tweet Prediction API is running"}
