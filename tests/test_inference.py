from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from catboost import CatBoostClassifier


MODEL_PATH = Path("outputs/catboost_model.cbm")
FEATURE_COLUMNS = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]


@pytest.fixture(scope="module")
def model():
    """Load trained model once for all tests."""
    if not MODEL_PATH.exists():
        pytest.skip("Model file not found — run pipeline first")
    m = CatBoostClassifier()
    m.load_model(str(MODEL_PATH))
    return m


class TestModelInference:
    def test_model_loads(self, model):
        assert model is not None

    def test_predict_returns_binary(self, model):
        row = pd.DataFrame([{col: 0.0 for col in FEATURE_COLUMNS}])
        pred = model.predict(row)[0]
        assert pred in (0, 1, 0.0, 1.0)

    def test_predict_proba_shape(self, model):
        row = pd.DataFrame([{col: 0.0 for col in FEATURE_COLUMNS}])
        proba = model.predict_proba(row)
        assert proba.shape == (1, 2)
        assert 0.0 <= proba[0][1] <= 1.0

    def test_batch_predict(self, model):
        rows = pd.DataFrame(
            np.zeros((10, len(FEATURE_COLUMNS))), columns=FEATURE_COLUMNS
        )
        preds = model.predict(rows)
        assert len(preds) == 10

    def test_feature_count_matches(self, model):
        expected = len(FEATURE_COLUMNS)
        assert model.feature_names_ is None or len(model.feature_names_) == expected
