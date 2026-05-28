from __future__ import annotations

import logging
from typing import List

import pandas as pd
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)

EXPECTED_COLUMNS: List[str] = [
    "Time",
    *[f"V{i}" for i in range(1, 29)],
    "Amount",
    "Class",
]


class TransactionSchema(BaseModel):
    """Pydantic model for a single transaction row."""
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
    Class: int

    @field_validator("Class")
    @classmethod
    def class_must_be_binary(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError(f"Class must be 0 or 1, got {v}")
        return v


def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validate DataFrame columns, types, and nulls. Return clean rows."""
    missing = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    extra = set(df.columns) - set(EXPECTED_COLUMNS)
    if extra:
        logger.warning("Extra columns will be ignored: %s", extra)

    null_count = df[EXPECTED_COLUMNS].isnull().sum().sum()
    if null_count > 0:
        logger.warning("Found %d null values — dropping rows with nulls", null_count)
        df = df.dropna(subset=EXPECTED_COLUMNS)

    # Validate Class column is binary
    bad_class = ~df["Class"].isin([0, 1])
    if bad_class.any():
        logger.warning("Dropping %d rows with invalid Class values", bad_class.sum())
        df = df[~bad_class]

    # Validate numeric types for feature columns
    numeric_cols = [c for c in EXPECTED_COLUMNS if c != "Class"]
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise TypeError(f"Column {col} must be numeric, got {df[col].dtype}")

    # Spot-check a sample with Pydantic for schema correctness
    sample = df.head(5)
    for idx, row in sample.iterrows():
        TransactionSchema(**row[EXPECTED_COLUMNS].to_dict())
    logger.info("Pydantic spot-check passed on %d sample rows", len(sample))

    df = df.reset_index(drop=True)
    logger.info("Validation passed: %d rows retained", len(df))
    return df
