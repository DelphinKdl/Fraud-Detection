"""FastAPI serving layer for fraud detection model.

Usage:
    uvicorn src.api.app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

import pandas as pd
from catboost import CatBoostClassifier
from fastapi import FastAPI, HTTPException

from src.api.schemas import (
    BatchRequest,
    BatchResponse,
    HealthResponse,
    PredictionResponse,
    TransactionRequest,
)
from src.config import load_config

logger = logging.getLogger(__name__)

config = load_config("config/config.yaml")

FEATURE_COLUMNS = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]

model: CatBoostClassifier | None = None
model_version: str = "unknown"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup."""
    global model, model_version
    model_path = Path(config.outputs.model_dir) / f"catboost_model.{config.outputs.model_format}"
    if model_path.exists():
        model = CatBoostClassifier()
        model.load_model(str(model_path))
        model_version = str(model_path.stat().st_mtime)
        logger.info("Model loaded: %s (modified: %s)", model_path, model_version)
    else:
        logger.error("Model file not found: %s", model_path)
    yield


app = FastAPI(
    title="Fraud Detection API",
    description="Real-time fraud scoring with CatBoost",
    version="1.0.0",
    lifespan=lifespan,
)


def _predict_single(txn: TransactionRequest) -> PredictionResponse:
    """Run prediction on a single transaction."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    features = pd.DataFrame([txn.model_dump()])[FEATURE_COLUMNS]
    pred = int(model.predict(features)[0])
    proba = float(model.predict_proba(features)[0][1])
    return PredictionResponse(prediction=pred, probability=round(proba, 6))


@app.post("/predict", response_model=PredictionResponse)
def predict(txn: TransactionRequest) -> PredictionResponse:
    """Score a single transaction."""
    start = time.time()
    result = _predict_single(txn)
    latency = (time.time() - start) * 1000
    logger.info("Prediction: %d (prob=%.4f, latency=%.1fms)", result.prediction, result.probability, latency)
    return result


@app.post("/predict/batch", response_model=BatchResponse)
def predict_batch(batch: BatchRequest) -> BatchResponse:
    """Score a batch of transactions."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start = time.time()
    rows = [txn.model_dump() for txn in batch.transactions]
    features = pd.DataFrame(rows)[FEATURE_COLUMNS]

    preds = model.predict(features).astype(int)
    probas = model.predict_proba(features)[:, 1]

    results = [
        PredictionResponse(prediction=int(p), probability=round(float(pr), 6))
        for p, pr in zip(preds, probas)
    ]
    latency = (time.time() - start) * 1000
    logger.info("Batch: %d transactions, latency=%.1fms", len(rows), latency)
    return BatchResponse(predictions=results)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        model_loaded=model is not None,
        model_version=str(model_version),
    )


@app.get("/metrics")
def metrics() -> dict:
    """Return saved evaluation metrics."""
    metrics_path = Path(config.outputs.metrics_path)
    if not metrics_path.exists():
        raise HTTPException(status_code=404, detail="Metrics file not found")
    with open(metrics_path) as f:
        return json.load(f)
