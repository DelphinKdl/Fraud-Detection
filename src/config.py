from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml

logger = logging.getLogger(__name__)


@dataclass
class DataConfig:
    raw_path: str = "data/raw/creditcard.parquet"
    processed_path: str = "data/processed/creditcard_clean.parquet"
    target_column: str = "Class"


@dataclass
class PreprocessingConfig:
    remove_duplicates: bool = True


@dataclass
class SplittingConfig:
    test_size: float = 0.20
    random_seed: int = 42
    stratify: bool = True


@dataclass
class SearchSpaceConfig:
    learning_rate: List[float] = field(default_factory=lambda: [0.01, 0.2])
    depth: List[int] = field(default_factory=lambda: [3, 8])
    l2_leaf_reg: List[float] = field(default_factory=lambda: [0.5, 5.0])


@dataclass
class ModelConfig:
    type: str = "catboost"
    optuna_trials: int = 10
    cv_folds: int = 3
    max_iterations: int = 1000
    early_stopping_rounds: int = 100
    random_seed: int = 42
    search_space: SearchSpaceConfig = field(default_factory=SearchSpaceConfig)


@dataclass
class OutputsConfig:
    model_dir: str = "outputs"
    metrics_path: str = "outputs/metrics.json"
    model_format: str = "cbm"


@dataclass
class ApiConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    model_version: str = "latest"


@dataclass
class DashboardConfig:
    port: int = 8501


@dataclass
class Config:
    data: DataConfig = field(default_factory=DataConfig)
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    splitting: SplittingConfig = field(default_factory=SplittingConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    outputs: OutputsConfig = field(default_factory=OutputsConfig)
    api: ApiConfig = field(default_factory=ApiConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)


def _build_nested(cls, data: dict):
    """Recursively build a dataclass from a nested dict."""
    if data is None:
        return cls()
    field_types = {f.name: f.type for f in cls.__dataclass_fields__.values()}
    kwargs = {}
    for key, value in data.items():
        if key in field_types:
            ft = field_types[key]
            # Resolve string annotations to actual classes in this module
            if isinstance(ft, str):
                ft = globals().get(ft, ft)
            if isinstance(ft, type) and hasattr(ft, "__dataclass_fields__") and isinstance(value, dict):
                kwargs[key] = _build_nested(ft, value)
            else:
                kwargs[key] = value
    return cls(**kwargs)


def load_config(path: str | Path) -> Config:
    """Load Config from a YAML file."""
    path = Path(path)
    if not path.exists():
        logger.warning("Config file %s not found, using defaults", path)
        return Config()
    with open(path) as f:
        raw = yaml.safe_load(f) or {}
    logger.info("Loaded config from %s", path)
    return _build_nested(Config, raw)
