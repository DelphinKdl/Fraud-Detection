from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def load_data(path: str | Path) -> pd.DataFrame:
    """Load a parquet or CSV file and log its schema."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    if path.suffix == ".parquet":
        df = pd.read_parquet(path)
    elif path.suffix == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

    logger.info("Loaded %s — shape: %s", path.name, df.shape)
    logger.info("Columns: %s", list(df.columns))
    logger.info("Dtypes:\n%s", df.dtypes.to_string())
    logger.info("Nulls: %d", df.isnull().sum().sum())
    return df
