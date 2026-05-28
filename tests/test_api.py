import pytest
from fastapi.testclient import TestClient

from src.api.app import app


def _sample_transaction() -> dict:
    """Return a sample transaction payload."""
    payload = {"Time": 0.0, "Amount": 149.62}
    for i in range(1, 29):
        payload[f"V{i}"] = 0.0
    return payload


@pytest.fixture(scope="module")
def client():
    """TestClient as context manager to trigger lifespan (model loading)."""
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "model_loaded" in data

    def test_health_model_loaded(self, client):
        resp = client.get("/health")
        assert resp.json()["model_loaded"] is True


class TestPredictEndpoint:
    def test_predict_returns_200(self, client):
        resp = client.post("/predict", json=_sample_transaction())
        assert resp.status_code == 200

    def test_predict_response_schema(self, client):
        resp = client.post("/predict", json=_sample_transaction())
        data = resp.json()
        assert "prediction" in data
        assert "probability" in data
        assert data["prediction"] in (0, 1)
        assert 0.0 <= data["probability"] <= 1.0

    def test_predict_missing_field_returns_422(self, client):
        payload = _sample_transaction()
        del payload["V1"]
        resp = client.post("/predict", json=payload)
        assert resp.status_code == 422


class TestBatchEndpoint:
    def test_batch_predict(self, client):
        batch = {"transactions": [_sample_transaction() for _ in range(3)]}
        resp = client.post("/predict/batch", json=batch)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["predictions"]) == 3


class TestMetricsEndpoint:
    def test_metrics_returns_200(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "precision" in data
        assert "recall" in data
        assert "f1" in data
