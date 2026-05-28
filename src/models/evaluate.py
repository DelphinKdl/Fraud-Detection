from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from src.config import Config

logger = logging.getLogger(__name__)


def evaluate_model(
    model: CatBoostClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    config: Config,
) -> dict:
    """Evaluate model, log metrics, save to outputs/metrics.json."""
    y_pred = model.predict(X_test)

    metrics = {
        "precision": float(precision_score(y_test, y_pred, pos_label=1)),
        "recall": float(recall_score(y_test, y_pred, pos_label=1)),
        "f1": float(f1_score(y_test, y_pred, pos_label=1)),
        "f1_macro": float(f1_score(y_test, y_pred, average="macro")),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "test_samples": int(len(y_test)),
        "test_fraud": int(y_test.sum()),
    }

    logger.info("--- Evaluation Results ---")
    logger.info("Precision : %.4f", metrics["precision"])
    logger.info("Recall    : %.4f", metrics["recall"])
    logger.info("F1 (fraud): %.4f", metrics["f1"])
    logger.info("F1 (macro): %.4f", metrics["f1_macro"])
    logger.info("\n%s", classification_report(y_test, y_pred))

    # Save to JSON
    metrics_path = Path(config.outputs.metrics_path)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Metrics saved to %s", metrics_path)

    return metrics
