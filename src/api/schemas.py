from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class TransactionRequest(BaseModel):
    """Single transaction for prediction."""
    Time: float
    V1: float
    V2: float
    V3: float
    V4: float
    V5: float
    V6: float
    V7: float
    V8: float
    V9: float
    V10: float
    V11: float
    V12: float
    V13: float
    V14: float
    V15: float
    V16: float
    V17: float
    V18: float
    V19: float
    V20: float
    V21: float
    V22: float
    V23: float
    V24: float
    V25: float
    V26: float
    V27: float
    V28: float
    Amount: float

    class Config:
        json_schema_extra = {
            "example": {
                "Time": 0.0,
                **{f"V{i}": 0.0 for i in range(1, 29)},
                "Amount": 149.62,
            }
        }


class PredictionResponse(BaseModel):
    """Single prediction result."""
    prediction: int = Field(description="0 = legitimate, 1 = fraud")
    probability: float = Field(description="Fraud probability score")


class BatchRequest(BaseModel):
    """Batch of transactions."""
    transactions: List[TransactionRequest]


class BatchResponse(BaseModel):
    """Batch prediction results."""
    predictions: List[PredictionResponse]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    model_version: str
