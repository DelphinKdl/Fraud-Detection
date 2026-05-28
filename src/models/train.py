from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
import optuna

from src.config import Config

logger = logging.getLogger(__name__)


def _objective(
    trial: optuna.Trial,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    config: Config,
) -> float:
    """Optuna objective: 3-fold stratified CV with macro F1."""
    np.random.seed(config.model.random_seed)
    search = config.model.search_space

    params = {
        "learning_rate": trial.suggest_float("learning_rate", search.learning_rate[0], search.learning_rate[1]),
        "depth": trial.suggest_int("depth", search.depth[0], search.depth[1]),
        "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", search.l2_leaf_reg[0], search.l2_leaf_reg[1]),
        "iterations": config.model.max_iterations,
        "loss_function": "Logloss",
        "eval_metric": "F1",
        "verbose": 0,
    }

    cv = StratifiedKFold(
        n_splits=config.model.cv_folds,
        shuffle=True,
        random_state=config.model.random_seed,
    )
    f1_scores = []
    best_iterations = []

    for train_idx, val_idx in cv.split(X_train, y_train):
        x_tr, x_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]

        model = CatBoostClassifier(**params, random_seed=config.model.random_seed)
        model.fit(
            x_tr, y_tr,
            eval_set=(x_val, y_val),
            early_stopping_rounds=config.model.early_stopping_rounds,
            use_best_model=True,
        )

        y_pred = model.predict(x_val)
        f1_scores.append(f1_score(y_val, y_pred, average="macro"))
        best_iterations.append(model.get_best_iteration())

    trial.set_user_attr("best_iteration", int(np.mean(best_iterations)))
    return np.mean(f1_scores)


def train_catboost(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    config: Config,
) -> CatBoostClassifier:
    """Run Optuna study, train final model with best params, save to outputs/."""
    logger.info(
        "Starting Optuna search: %d trials, %d-fold CV",
        config.model.optuna_trials,
        config.model.cv_folds,
    )

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=config.model.random_seed),
    )
    study.optimize(
        lambda trial: _objective(trial, X_train, y_train, config),
        n_trials=config.model.optuna_trials,
    )

    best = study.best_trial
    logger.info("Best CV F1: %.4f", best.value)
    logger.info("Best params: %s", best.params)
    logger.info("Best iterations: %d", best.user_attrs["best_iteration"])

    # Train final model on full training data
    final_params = best.params.copy()
    final_params["iterations"] = best.user_attrs["best_iteration"]
    final_params["verbose"] = 0

    final_model = CatBoostClassifier(
        **final_params, random_seed=config.model.random_seed
    )
    final_model.fit(X_train, y_train)

    # Save model with version tag
    out_dir = Path(config.outputs.model_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = out_dir / f"catboost_model_{version}.{config.outputs.model_format}"
    latest_path = out_dir / f"catboost_model.{config.outputs.model_format}"

    final_model.save_model(str(model_path))
    final_model.save_model(str(latest_path))
    logger.info("Model saved: %s (+ latest)", model_path)

    return final_model
