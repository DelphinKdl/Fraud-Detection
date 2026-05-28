from __future__ import annotations

import logging
from typing import Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import Config

logger = logging.getLogger(__name__)


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicate rows."""
    n_before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    n_removed = n_before - len(df)
    logger.info("Removed %d duplicates (%d → %d rows)", n_removed, n_before, len(df))
    return df


def get_feature_columns(df: pd.DataFrame, target: str = "Class") -> list[str]:
    """Return all columns except the target."""
    features = [col for col in df.columns if col != target]
    logger.info("Feature columns (%d): %s", len(features), features)
    return features


def split_data(
    df: pd.DataFrame, config: Config
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Stratified train/test split based on config."""
    target = config.data.target_column
    X = df.drop(columns=[target])
    y = df[target]

    stratify = y if config.splitting.stratify else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=config.splitting.test_size,
        random_state=config.splitting.random_seed,
        stratify=stratify,
    )

    logger.info(
        "Split: train=%d, test=%d | Fraud in test: %d",
        len(X_train),
        len(X_test),
        y_test.sum(),
    )
    return X_train, X_test, y_train, y_test
