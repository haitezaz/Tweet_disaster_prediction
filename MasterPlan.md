# Confidence-Aware Disaster Alert System  
DS201 – Programming for AI  
Semester Project Master Plan

---

## 1. Project Overview

This project implements an end-to-end AI system that detects real-world disaster-related tweets while explicitly handling uncertainty to prevent false alarms.

Rather than relying on a single model, the system uses a **two-model decision pipeline** with confidence-based routing and rejection. The goal is not maximum accuracy, but **safe, reliable, and reproducible decision-making**, aligned with real-world deployment constraints.

The system evolves incrementally across Assignments 1–3 and culminates in a Dockerized AI service with basic MLOps readiness.

---

## 2. Core Problem Statement

Social media platforms contain large volumes of disaster-related language that is often metaphorical (e.g., “this exam is a disaster”, “this song is fire”).

False positives can cause unnecessary panic, while false negatives may delay emergency response.

Therefore, the system must:
- Detect real disaster-related tweets
- Quantify prediction confidence
- Refuse or escalate decisions when uncertainty is high

This motivates a **confidence-aware, multi-model AI system** rather than a single prediction script.

---

## 3. Dataset

**Dataset:** NLP with Disaster Tweets (Kaggle)  
**Type:** Tabular + Text  
**Task:** Binary classification (Disaster vs Not Disaster)

### Reasons for Selection
- Real-world, noisy text data
- High semantic ambiguity
- Clear risk associated with false positives
- Suitable for confidence-based rejection
- Manageable complexity for reproducibility and deployment

---

## 4. System Architecture (High-Level)
```
Tweet Input
↓
Text Preprocessing
↓
Primary Model (Model A)
↓
Confidence Evaluation
├── High confidence → Accept decision
├── Medium confidence → Fallback Model (Model B)
└── Low confidence → Reject / Manual Review
```

This architecture ensures that uncertainty is treated as a first-class concern rather than a failure.

---

## 5. Model Design

### 5.1 Model A – Primary Model (Sensitive)

**Purpose:**  
Maximize detection of real disasters (high recall).

**Model Choices:**
- Logistic Regression OR Linear SVM

**Input Representation:**
- TF-IDF vectorized tweet text

**Characteristics:**
- More sensitive
- Higher recall
- Can produce uncertain predictions

---

### 5.2 Model B – Fallback Model (Conservative)

**Purpose:**  
Confirm disaster predictions only when evidence is strong.

**Model Choices:**
- Multinomial Naive Bayes OR
- Shallow Decision Tree

**Characteristics:**
- More conservative
- Lower false-positive rate
- Used only when Model A is uncertain

---

## 6. Decision Logic & Confidence Routing

Confidence thresholds are explicitly defined and configurable.

Example logic:

- If confidence ≥ 0.85  
  → Accept Model A prediction

- If 0.60 ≤ confidence < 0.85  
  → Invoke Model B  
    - If Model B agrees → Accept  
    - If Model B disagrees → Reject

- If confidence < 0.60  
  → Reject and mark as “Uncertain”

Rejection is treated as a **safe system behavior**, not an error.

---

## 7. Project Structure (Updated - Assignment 1 Complete)

```
ai_system_project/
├── data/
│   ├── raw/
│   │   ├── train.csv
│   │   └── test.csv
│   ├── processed/
│   └── README.md
│
├── config/
│   └── config.yaml                    # ✓ Centralized configuration
│
├── src/
│   ├── __init__.py
│   ├── data_work/
│   │   ├── __init__.py
│   │   ├── load_data.py               # ✓ Data loading module
│   │   ├── preprocess.py              # ✓ Preprocessing pipeline
│   │   └── test.py                    # Ad-hoc testing script
│   ├── features/
│   │   ├── __init__.py
│   │   └── feature_engineering.py     # ✓ TF-IDF feature extraction
│   ├── models/
│   │   ├── __init__.py
│   │   ├── model_config.py            # ✓ NEW: Model configurations
│   │   ├── train.py                   # ✓ Training pipeline
│   │   └── evaluate.py                # TODO: Assignment 2
│   └── utils/
│       ├── __init__.py
│       └── validation.py              # ✓ NEW: Data validation utilities
│
├── api/                                # TODO: Assignment 3
│   ├── main.py
│   ├── routes.py
│   └── schemas.py
│
├── tests/                              # TODO: Assignment 2 (pytest)
│   ├── test_preprocessing.ipynb       # Current exploratory tests
│   ├── test_models.ipynb
│   └── test_api.ipynb
│
├── artifacts/                          # ✓ Model artifacts directory
│   ├── model_baseline.pkl
│   ├── vectorizer.pkl
│   └── metrics_baseline.json
│
├── docker/                             # TODO: Assignment 3
│   └── Dockerfile
│
├── requirements.txt                    # ✓ Dependencies
├── README.md                           # ✓ Project documentation
└── MasterPlan.md                       # ✓ This file (updated)
```

**Key Modularization Principles Applied:**

1. **Separation of Concerns:**
   - Data loading ([`load_data.py`](src/data_work/load_data.py)) ≠ Preprocessing ([`preprocess.py`](src/data_work/preprocess.py))
   - Feature engineering ([`feature_engineering.py`](src/features/feature_engineering.py)) ≠ Model training ([`train.py`](src/models/train.py))
   - Model configuration ([`model_config.py`](src/models/model_config.py)) ≠ Training logic

2. **Reusability:**
   - [`validation.py`](src/utils/validation.py) provides utilities used across multiple modules
   - [`config.yaml`](config/config.yaml) centralizes all parameters for easy experimentation

3. **Reproducibility:**
   - Fixed random seeds in [`config.yaml`](config/config.yaml)
   - Comprehensive logging in [`train.py`](src/models/train.py)
   - Artifact versioning with timestamps

4. **Testability:**
   - Each module has a single responsibility
   - Validation utilities enable systematic testing (Assignment 2)

---

## 8. Assignment-by-Assignment Execution Plan

### Assignment 1 – Data & Pipeline Foundations ✓ COMPLETE

**Focus:** Thinking, data understanding, modularity

**Completed Deliverables:**
- ✓ Dataset selection & justification (Disaster Tweets)
- ✓ Exploratory Data Analysis (in notebooks)
- ✓ Modular preprocessing pipeline ([`preprocess.py`](src/data_work/preprocess.py))
- ✓ Baseline model (Logistic Regression in [`train.py`](src/models/train.py))
- ✓ Proper train/validation split with stratification
- ✓ Leakage checks ([`validation.py`](src/utils/validation.py))
- ✓ Configuration management ([`config.yaml`](config/config.yaml))

**Key Modules Created:**
- [`src/data_work/load_data.py`](src/data_work/load_data.py): CSV loading with path validation
- [`src/data_work/preprocess.py`](src/data_work/preprocess.py): Text cleaning & preprocessing
- [`src/features/feature_engineering.py`](src/features/feature_engineering.py): TF-IDF feature extraction
- [`src/models/train.py`](src/models/train.py): Training pipeline with logging
- [`src/models/model_config.py`](src/models/model_config.py): Centralized model configurations
- [`src/utils/validation.py`](src/utils/validation.py): Data validation utilities

**Current Model Performance:**
- Baseline: Logistic Regression with TF-IDF features
- Validation accuracy logged in `artifacts/metrics_baseline.json`

**Report Topics (Handwritten, 3 pages):**
- ✓ Problem framing & system perspective
- ✓ Data assumptions vs reality (class imbalance, noisy text)
- ✓ Pipeline design decisions (modular architecture)
- ✓ One real failure & debugging story
- ✓ Reflection on redesign choices

---

### Assignment 2 – Evaluation, Testing & Reproducibility (IN PROGRESS)

**Focus:** Engineering discipline & evaluation rigor

**Planned Deliverables:**
- Two models (Model A: Logistic Regression + Model B: TBD)
- Multiple evaluation metrics (accuracy, precision, recall, F1)
- Error analysis module
- Model serialization (already implemented in [`train.py`](src/models/train.py))
- Reproducibility controls (seeds in [`config.yaml`](config/config.yaml))
- Unit tests (pytest - TODO)

**Modules to Create:**
- `src/models/evaluate.py`: Comprehensive evaluation logic
- `tests/test_preprocessing.py`: Unit tests for preprocessing
- `tests/test_models.py`: Unit tests for model training
- `tests/test_validation.py`: Tests for validation utilities

**Report (Handwritten, 3–4 pages):**
- Metric justification
- Error & failure patterns
- Reproducibility issues
- Accuracy vs simplicity trade-offs
- Surprising or misleading results

---

### Assignment 3 – Model as a Service (TODO)

**Focus:** API design, deployment readiness

**Planned Deliverables:**
- FastAPI application ([`api/main.py`](api/main.py))
- RESTful endpoints ([`api/routes.py`](api/routes.py))
- Input validation schemas ([`api/schemas.py`](api/schemas.py))
- Dockerization ([`docker/Dockerfile`](docker/Dockerfile))
- Health checks & monitoring

**API Features:**
- `/predict`: Single prediction endpoint
- `/batch_predict`: Batch inference
- `/model_info`: Model metadata
- `/health`: Service health check

---

### Final Project – Deployment & Operational Readiness (TODO)

**Focus:** Production-grade system with confidence-based routing

**Planned Deliverables:**
- Two-model architecture (Model A + Model B)
- Confidence-based decision routing
- Containerized deployment
- Monitoring & logging
- Documentation & demo

---

## 9. Evaluation Philosophy Alignment

This project explicitly aligns with course philosophy:

- System design > model accuracy
- Engineering maturity > algorithm novelty
- Reproducibility > leaderboard chasing
- Honest failures > silent hacks

Uncertainty handling and rejection are treated as strengths.

---

## 10. Key Design Principles

**Modularity:**
- Each file has a single, well-defined responsibility
- Functions are small, testable, and reusable
- Configuration is separated from code

**Reproducibility:**
- Fixed random seeds ([`config.yaml`](config/config.yaml))
- Versioned artifacts with timestamps
- Comprehensive logging in training pipeline

**Transparency:**
- Validation checks prevent silent failures ([`validation.py`](src/utils/validation.py))
- Feature importance extraction for interpretability
- Explicit preprocessing steps documented in code

**Scalability:**
- Factory pattern for model instantiation ([`model_config.py`](src/models/model_config.py))
- Configurable hyperparameters via YAML
- Modular architecture supports easy extension

---

## 11. One-Sentence Project Summary

"A confidence-aware disaster tweet classification system that routes predictions through primary and fallback models based on prediction uncertainty, prioritizing both accuracy and operational transparency in critical alerting scenarios."

---

## Appendix: Module Dependency Graph

```
config.yaml
    ↓
load_data.py → validation.py
    ↓              ↓
preprocess.py → validation.py
    ↓
feature_engineering.py
    ↓
model_config.py → train.py → artifacts/
```

---

**Last Updated:** [Current Date]  
**Assignment 1 Status:** ✓ Complete  
**Assignment 2 Status:** In Progress  
**Next Milestone:** Implement `evaluate.py` and pytest test suite
