import pandas as pd
import pytest

from src.data.validation import EXPECTED_COLUMNS, TransactionSchema, validate_dataframe


def _make_valid_row() -> dict:
    """Create a single valid transaction row."""
    row = {"Time": 0.0, "Amount": 100.0, "Class": 0}
    for i in range(1, 29):
        row[f"V{i}"] = 0.0
    return row


class TestTransactionSchema:
    def test_valid_row(self):
        row = _make_valid_row()
        txn = TransactionSchema(**row)
        assert txn.Class == 0

    def test_invalid_class(self):
        row = _make_valid_row()
        row["Class"] = 5
        with pytest.raises(ValueError):
            TransactionSchema(**row)

    def test_missing_field(self):
        row = _make_valid_row()
        del row["V1"]
        with pytest.raises(Exception):
            TransactionSchema(**row)


class TestValidateDataframe:
    def test_valid_df(self):
        rows = [_make_valid_row() for _ in range(10)]
        df = pd.DataFrame(rows)
        result = validate_dataframe(df)
        assert len(result) == 10

    def test_missing_column_raises(self):
        rows = [_make_valid_row() for _ in range(5)]
        df = pd.DataFrame(rows).drop(columns=["V1"])
        with pytest.raises(ValueError, match="Missing columns"):
            validate_dataframe(df)

    def test_drops_null_rows(self):
        rows = [_make_valid_row() for _ in range(5)]
        df = pd.DataFrame(rows)
        df.loc[0, "V1"] = None
        result = validate_dataframe(df)
        assert len(result) == 4

    def test_drops_invalid_class(self):
        rows = [_make_valid_row() for _ in range(5)]
        df = pd.DataFrame(rows)
        df.loc[0, "Class"] = 3
        result = validate_dataframe(df)
        assert len(result) == 4
