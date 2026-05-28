"""Feast feature store integration for fraud detection.

Provides offline materialization and online feature retrieval
using Feast with a PostgreSQL online store.

Usage:
    # Materialize features to online store
    python -m src.features.store --materialize

    # Retrieve features for a transaction
    python -m src.features.store --get-online 12345
"""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from feast import FeatureStore

logger = logging.getLogger(__name__)

FEATURE_REPO_PATH = "feature_store/feature_repo"
FEATURE_SERVICE = "transaction_features"
FEATURE_COLUMNS = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]


def get_store(repo_path: str = FEATURE_REPO_PATH) -> FeatureStore:
    """Initialize Feast feature store."""
    return FeatureStore(repo_path=repo_path)


def prepare_offline_data(input_path: str, output_path: str) -> pd.DataFrame:
    """Prepare processed data for Feast ingestion.

    Adds transaction_id and event_timestamp columns required by Feast.
    """
    df = pd.read_parquet(input_path)
    df["transaction_id"] = range(len(df))
    df["event_timestamp"] = pd.Timestamp.now() - pd.to_timedelta(
        range(len(df) - 1, -1, -1), unit="s"
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output, index=False)
    logger.info("Prepared %d rows for Feast → %s", len(df), output)
    return df


def apply_feature_store(repo_path: str = FEATURE_REPO_PATH) -> None:
    """Apply Feast feature definitions (register features)."""
    store = get_store(repo_path)
    store.apply([])  # Apply all objects discovered in the repo
    logger.info("Feature store applied successfully")


def materialize_features(
    repo_path: str = FEATURE_REPO_PATH,
    start: datetime | None = None,
    end: datetime | None = None,
) -> None:
    """Materialize features from offline store to online store (PostgreSQL)."""
    store = get_store(repo_path)
    if end is None:
        end = datetime.now()
    if start is None:
        start = end - timedelta(days=7)
    store.materialize(start_date=start, end_date=end)
    logger.info("Materialized features from %s to %s", start, end)


def get_online_features(
    transaction_ids: list[int],
    repo_path: str = FEATURE_REPO_PATH,
) -> pd.DataFrame:
    """Retrieve features from online store for real-time inference.

    Args:
        transaction_ids: List of transaction IDs to fetch features for.
        repo_path: Path to Feast feature repo.

    Returns:
        DataFrame with features for the requested transactions.
    """
    store = get_store(repo_path)
    entity_rows = [{"transaction_id": tid} for tid in transaction_ids]
    features = [
        f"{FEATURE_SERVICE}:{col}" for col in FEATURE_COLUMNS
    ]
    feature_vector = store.get_online_features(
        features=features,
        entity_rows=entity_rows,
    )
    return feature_vector.to_df()


def get_historical_features(
    entity_df: pd.DataFrame,
    repo_path: str = FEATURE_REPO_PATH,
) -> pd.DataFrame:
    """Retrieve historical features for training from offline store.

    Args:
        entity_df: DataFrame with transaction_id and event_timestamp columns.
        repo_path: Path to Feast feature repo.

    Returns:
        DataFrame with historical features joined to entities.
    """
    store = get_store(repo_path)
    features = [
        f"{FEATURE_SERVICE}:{col}" for col in FEATURE_COLUMNS
    ]
    training_df = store.get_historical_features(
        entity_df=entity_df,
        features=features,
    )
    return training_df.to_df()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description="Feast feature store operations")
    parser.add_argument("--prepare", action="store_true", help="Prepare offline data for Feast")
    parser.add_argument("--materialize", action="store_true", help="Materialize to online store")
    parser.add_argument("--get-online", type=int, nargs="+", help="Get online features for transaction IDs")
    args = parser.parse_args()

    if args.prepare:
        prepare_offline_data(
            "data/processed/creditcard_clean.parquet",
            "data/processed/creditcard_features.parquet",
        )
    elif args.materialize:
        materialize_features()
    elif args.get_online:
        df = get_online_features(args.get_online)
        print(df)
    else:
        parser.print_help()
