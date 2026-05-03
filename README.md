# Tweet disaster prediction

A REST API that classifies tweet text as disaster-related or not, using a confidence-aware ensemble of scikit-learn models. It is intended for developers and researchers who need a structured, persistence-backed inference endpoint. Predictions and raw requests are stored in Firebase Data Connect (Cloud SQL via GraphQL) and surfaced through a built-in monitoring dashboard.

## Table of contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Running tests](#running-tests)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Architecture

```
Tweet_disaster_prediction/
├── api/
│   ├── main.py          # FastAPI application factory and lifespan handler
│   ├── routes.py        # All HTTP route definitions
│   ├── crud.py          # Firebase Data Connect mutation and query wrappers
│   ├── database.py      # Async HTTP client for Firebase Data Connect REST API
│   ├── schemas.py       # Pydantic request/response models
│   ├── templates/       # Server-rendered dashboard HTML
│   └── static/          # Dashboard CSS and JS assets
├── src/
│   ├── config.py        # Central configuration (thresholds, env vars)
│   ├── models/
│   │   ├── decision_engine.py  # Confidence-aware LR + Naive Bayes ensemble
│   │   ├── train.py            # Model training script
│   │   └── evaluate.py         # Evaluation utilities
│   ├── features/        # Feature engineering
│   ├── data_work/       # Data loading and preprocessing
│   └── utils/           # Logging and shared helpers
├── artifacts/           # Serialized model files (.pkl); required at runtime
├── tests/
│   ├── test_api.py      # End-to-end API tests (mocked Firebase and engine)
│   ├── test_pipeline.py # ML pipeline unit tests
│   └── stress_test.py   # Async load test against a live server
├── docker/
│   └── Dockerfile       # Container image definition
├── dataconnect/         # Firebase Data Connect schema and connector config
├── .env.example         # Environment variable template
└── requirements.txt
```

The `DecisionEngine` applies Logistic Regression as the primary classifier. When the predicted probability falls in an uncertain band (0.25–0.75), it delegates to a Naive Bayes fallback. The chosen model and its confidence score are returned in every response as `source` and `confidence` fields.

## Prerequisites

- Python >= 3.12
- pip
- A Firebase project with Firebase Data Connect enabled and a Cloud SQL instance provisioned
- A Google Cloud service account with the `Cloud Datastore User` and `Firebase Data Connect` IAM roles (or equivalent)

## Installation

1. Clone the repository.

```bash
git clone <repository-url>
cd Tweet_disaster_prediction
```

2. Create and activate a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Copy the environment variable template and fill in the required values.

```bash
cp .env.example .env
```

5. Place serialized model artifacts in the `artifacts/` directory. The following three files are required:

```
artifacts/logistic_regression.pkl
artifacts/naive_bayes.pkl
artifacts/tfidf_vectorizer.pkl
```

<!-- Artifact generation: run `python -m src.models.train` after sourcing training data into data/ -->

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `FIREBASE_PROJECT_ID` | Yes | `tweet-disaster-prediction` | GCP project ID that hosts the Firebase Data Connect service |
| `FIREBASE_LOCATION` | Yes | `us-east4` | Region where the Data Connect service is deployed |
| `DATA_CONNECT_SERVICE_ID` | Yes | `tweetdisasterprediction` | Data Connect service identifier |
| `DATA_CONNECT_CONNECTOR_ID` | Yes | `example` | Data Connect connector identifier |
| `FIREBASE_CREDENTIALS_JSON` | Yes* | — | Raw JSON content of a service account key. Takes precedence over `GOOGLE_APPLICATION_CREDENTIALS` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes* | — | Absolute path to a service account key file. Used when `FIREBASE_CREDENTIALS_JSON` is not set |

\* At least one of `FIREBASE_CREDENTIALS_JSON` or `GOOGLE_APPLICATION_CREDENTIALS` must be supplied. If neither is set, the client falls back to Application Default Credentials.

## Usage

**Start the development server**

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Classify a tweet**

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Earthquake hits downtown, buildings collapsing"}'
```

Example response:

```json
{
  "request_id": "uuid-...",
  "prediction_id": "uuid-...",
  "disaster": true,
  "confidence": 0.912,
  "source": "logistic_regression",
  "event": {
    "location": "Unknown",
    "timestamp": "2026-05-03 06:29:00"
  }
}
```

**Classify with optional metadata**

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Flood reported near the river bank",
    "location": "Lahore",
    "event_timestamp": "2026-05-03T06:00:00Z"
  }'
```

**Check service health**

```bash
curl http://localhost:8000/health
```

**Open the monitoring dashboard**

Navigate to `http://localhost:8000/dashboard` in a browser. The dashboard shows prediction volume over time, disaster rate, average confidence, and a recent-predictions feed. Query parameters:

| Parameter | Default | Range | Description |
|---|---|---|---|
| `window_minutes` | 60 | 5–1440 | Lookback window in minutes |
| `bucket_minutes` | 5 | 1–60 | Time-series bucket width in minutes |
| `recent_limit` | 20 | 5–100 | Number of recent predictions to return |

**Interactive API docs**

```
http://localhost:8000/docs
```

## Running tests

**Unit and integration tests**

```bash
pytest tests/test_api.py tests/test_pipeline.py -v
```

Firebase and the `DecisionEngine` are mocked; no live credentials or artifacts are required for these tests.

**Async concurrency test (requires live server and artifacts)**

```bash
# Start the server first, then:
python tests/stress_test.py
```

The stress test sends 100 requests at a concurrency limit of 20 and reports total time, average latency, and throughput.

## Deployment

**Docker**

```bash
# Build the image
docker build -f docker/Dockerfile -t tweet-disaster-api .

# Run the container
docker run -p 8000:8000 \
  -e FIREBASE_PROJECT_ID=<project-id> \
  -e FIREBASE_LOCATION=<location> \
  -e DATA_CONNECT_SERVICE_ID=<service-id> \
  -e DATA_CONNECT_CONNECTOR_ID=<connector-id> \
  -e FIREBASE_CREDENTIALS_JSON='<raw-json>' \
  tweet-disaster-api
```

The image copies `api/`, `src/`, and `artifacts/` from the build context. Ensure the serialized model artifacts are present locally before building.

<!-- Cloud deployment: see deploy.log for Railway-specific configuration notes -->

## Contributing

1. Open an issue to describe the bug or proposed change before submitting a pull request.
2. Fork the repository and create a branch from `main`.
3. Keep changes focused; one logical change per pull request.
4. Ensure `pytest tests/test_api.py tests/test_pipeline.py` passes before requesting review.
5. Submit the pull request against `main` with a concise description of what was changed and why.

