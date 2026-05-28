import pandas as pd
import pytest

from src.features.engineering import remove_duplicates, split_data
from src.config import load_config


def _make_df(n: int = 100) -> pd.DataFrame:
    """Create a synthetic DataFrame."""
    import numpy as np
    np.random.seed(42)
    data = {"Time": np.random.rand(n), "Amount": np.random.rand(n) * 100}
    for i in range(1, 29):
        data[f"V{i}"] = np.random.randn(n)
    data["Class"] = [0] * (n - 5) + [1] * 5
    return pd.DataFrame(data)


class TestRemoveDuplicates:
    def test_no_duplicates(self):
        df = _make_df(50)
        result = remove_duplicates(df)
        assert len(result) == 50

    def test_removes_exact_duplicates(self):
        df = _make_df(10)
        df = pd.concat([df, df.iloc[:3]], ignore_index=True)
        result = remove_duplicates(df)
        assert len(result) == 10


class TestSplitData:
    def test_split_sizes(self):
        config = load_config("config/config.yaml")
        df = _make_df(100)
        X_train, X_test, y_train, y_test = split_data(df, config)
        assert len(X_train) + len(X_test) == 100
        assert len(X_train) == 80
        assert len(X_test) == 20

    def test_stratification_preserves_ratio(self):
        config = load_config("config/config.yaml")
        df = _make_df(200)
        df["Class"] = [0] * 190 + [1] * 10
        _, _, _, y_test = split_data(df, config)
        fraud_ratio = y_test.mean()
        assert 0.01 < fraud_ratio < 0.15

    def test_no_target_in_features(self):
        config = load_config("config/config.yaml")
        df = _make_df(50)
        X_train, X_test, _, _ = split_data(df, config)
        assert "Class" not in X_train.columns
        assert "Class" not in X_test.columns
