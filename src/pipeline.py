"""End-to-end training pipeline.

Usage:
    python -m src.pipeline --config config/config.yaml
"""
from __future__ import annotations

import argparse
import logging

from src.config import load_config
from src.data.ingestion import load_data
from src.data.validation import validate_dataframe
from src.features.engineering import remove_duplicates, split_data
from src.models.train import train_catboost
from src.models.evaluate import evaluate_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main(config_path: str = "config/config.yaml") -> None:
    """Run the full pipeline: ingest → validate → engineer → train → evaluate."""
    logger.info("=== Fraud Detection Pipeline ===")

    # 1. Load config
    config = load_config(config_path)
    logger.info("Config loaded from %s", config_path)

    # 2. Ingest data
    df = load_data(config.data.raw_path)

    # 3. Validate schema
    df = validate_dataframe(df)

    # 4. Remove duplicates
    if config.preprocessing.remove_duplicates:
        df = remove_duplicates(df)

    # 5. Train/test split
    X_train, X_test, y_train, y_test = split_data(df, config)

    # 6. Train CatBoost + Optuna
    model = train_catboost(X_train, y_train, config)

    # 7. Evaluate
    metrics = evaluate_model(model, X_test, y_test, config)

    logger.info("=== Pipeline complete ===")
    logger.info("F1 (fraud): %.4f | Precision: %.4f | Recall: %.4f",
                metrics["f1"], metrics["precision"], metrics["recall"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fraud Detection Training Pipeline")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config YAML")
    args = parser.parse_args()
    main(args.config)
