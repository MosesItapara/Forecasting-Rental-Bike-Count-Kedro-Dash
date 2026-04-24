# 🚲 Forecasting Rental Bike Count

[![Powered by Kedro](https://img.shields.io/badge/powered_by-kedro-ffc900?logo=kedro)](https://kedro.org)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A machine learning application that forecasts the number of rented bikes for the next hour using a real-time inference pipeline and an interactive Dash dashboard.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Running the Pipelines](#running-the-pipelines)
- [Dashboard](#dashboard)
- [Configuration](#configuration)
- [Docker Deployment](#docker-deployment)
- [Production Deployment (Railway)](#production-deployment-railway)
- [Testing](#testing)
- [Development Guidelines](#development-guidelines)

---

## Overview

This project uses [Kedro](https://kedro.org) to build and orchestrate three ML pipelines:

| Pipeline | Description |
|---|---|
| `feature_engineering` | Renames columns, generates lag features |
| `training` | Trains a CatBoost (or other) regression model |
| `inference` | Loads the model and generates predictions on new data |

Predictions are visualised in a real-time Dash dashboard that updates every second, simulating 1 hour of dataset time per tick.

---

## Architecture

```
Raw Data → Feature Engineering → Training → Model
                                              ↓
Inference Batch → Feature Engineering → Inference → Predictions → Dashboard
```

- The **UI app** and **inference pipeline** run in separate Docker containers
- **Data and models** are stored and shared via Docker volumes
- In production, the dashboard is served via **Railway**

---

## Project Structure

```
├── conf/
│   ├── base/
│   │   ├── catalog.yml          # Dataset definitions
│   │   ├── parameters.yml       # Pipeline parameters
│   │   └── logging.yml
│   └── local/                   # Local overrides (not committed)
├── data/
│   ├── 01_raw/                  # Raw input data
│   ├── 06_models/               # Saved models
│   └── 07_model_outputs/        # Predictions output
├── src/
│   └── forecasting_rental_bike_count/
│       ├── pipelines/           # Kedro pipeline definitions
│       └── app_ui/              # Dash dashboard
├── docker-compose.yml           # Multi-container orchestration
├── Dockerfile.inference         # Inference pipeline container
├── Dockerfile.dashboard         # Dash dashboard container
└── tests/
```

---

## Getting Started

### Prerequisites

- Python 3.12
- pip
- Docker & Docker Compose (for containerised deployment)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd forecasting-rental-bike-count

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

---

## Running the Pipelines

### Full training pipeline
```bash
kedro run
```

### Individual pipelines
```bash
kedro run --pipeline=feature_engineering
kedro run --pipeline=training
kedro run --pipeline=inference
```

### Resume from a failed node
```bash
kedro run --from-nodes "<node_name>"
```

---

## Dashboard

Start the Dash dashboard locally:

```bash
python src/app_ui/app.py
```

Then open your browser at [http://127.0.0.1:8050](http://127.0.0.1:8050).

**Features:**
- Real-time chart of predicted vs actual bike counts
- Adjustable lookback window (last N hours)
- Auto-refreshes every second

---

## Configuration

All pipeline parameters are defined in `conf/base/parameters.yml`:

```yaml
training:
  model_type: catboost        # catboost | random_forest | linear_regression
  train_fraction: 0.8
  model_params:
    catboost:
      learning_rate: 0.2
      depth: 6
      iterations: 50

model_storage:
  path: data/06_models
  name: forecast_model
```

Dataset paths are defined in `conf/base/catalog.yml`.

---

## Docker Deployment

The application runs as two containers orchestrated with Docker Compose:

| Container | Description |
|---|---|
| `inference` | Runs the Kedro inference pipeline on a schedule |
| `dashboard` | Serves the Dash UI on port 8050 |

Both containers share a Docker volume for data and model files.

### Build and run

```bash
docker-compose up --build
```

### Run in detached mode

```bash
docker-compose up -d --build
```

### Stop containers

```bash
docker-compose down
```

### View logs

```bash
docker-compose logs -f inference
docker-compose logs -f dashboard
```

### Example `docker-compose.yml`

```yaml
version: "3.8"

services:
  inference:
    build:
      context: .
      dockerfile: Dockerfile.inference
    volumes:
      - bike-data:/app/data
    restart: unless-stopped

  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.dashboard
    ports:
      - "8050:8050"
    volumes:
      - bike-data:/app/data
    depends_on:
      - inference
    restart: unless-stopped

volumes:
  bike-data:
```

### Example `Dockerfile.inference`

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["kedro", "run", "--pipeline=inference"]
```

### Example `Dockerfile.dashboard`

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8050
CMD ["python", "src/app_ui/app.py"]
```

---

## Production Deployment (Railway)

[Railway](https://railway.app) can be used to host the dashboard in production.

### Steps

1. Push your repository to GitHub
2. Create a new project on [railway.app](https://railway.app)
3. Connect your GitHub repository
4. Set the following environment variables in Railway:

| Variable | Value |
|---|---|
| `PORT` | `8050` |
| `KEDRO_DISABLE_TELEMETRY` | `true` |

5. Set the start command in Railway to:

```bash
python src/app_ui/app.py
```

6. Make sure your `app.py` reads the port from the environment:

```python
import os

port = int(os.environ.get("PORT", 8050))

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=port)
```

> **Note:** On Railway use `host="0.0.0.0"` so the app binds correctly to the container's network interface. Use `host="127.0.0.1"` for local development only.

### Persistent storage on Railway

Railway does not persist files between deploys by default. For production consider:
- Storing model files and predictions in a cloud storage bucket (e.g. AWS S3, Google Cloud Storage)
- Using a Railway volume if available on your plan

---

## Testing

```bash
pytest
```

Coverage is reported automatically. The threshold can be adjusted in `pyproject.toml` under `[tool.coverage.report]`.

---

## Development Guidelines

- Do not commit data files — they are listed in `.gitignore`
- Do not commit credentials or local config — use `conf/local/` for overrides
- Follow the [Kedro data engineering convention](https://docs.kedro.org/en/stable/faq/faq.html#what-is-data-engineering-convention) for dataset naming and folder structure
- Results should be fully reproducible from raw data using `kedro run`

---

## Useful Commands

| Command | Description |
|---|---|
| `kedro run` | Run the full pipeline |
| `kedro run --pipeline=inference` | Run inference only |
| `kedro viz` | Visualise the pipeline DAG |
| `kedro jupyter notebook` | Launch Jupyter with Kedro context |
| `kedro ipython` | Launch IPython with Kedro context |
| `pytest` | Run tests with coverage |
| `docker-compose up --build` | Build and start all containers |
| `docker-compose down` | Stop all containers |
