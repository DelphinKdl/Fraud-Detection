# Feature Store

Feast-based feature store with PostgreSQL online store for real-time feature retrieval during inference.

## Architecture

- **Offline Store**: Parquet files (`data/processed/creditcard_features.parquet`)
- **Online Store**: PostgreSQL (via docker-compose)
- **Entity**: `transaction_id` — unique identifier per transaction
- **Features**: V1–V28, Time, Amount (30 numeric features)

## Setup

```bash
# Start PostgreSQL (via Docker)
docker compose up -d postgres

# Prepare offline data (adds transaction_id + event_timestamp)
python -m src.features.store --prepare

# Apply feature definitions to Feast registry
feast -c feature_store/feature_repo apply

# Materialize features to online store
python -m src.features.store --materialize
```

## Usage

```python
from src.features.store import get_online_features

# Retrieve features for real-time inference
features_df = get_online_features(transaction_ids=[123, 456])
```

## Configuration

See `feature_store/feature_repo/feature_store.yaml` for Feast settings.
PostgreSQL connection uses environment variables:
- `POSTGRES_HOST` (default: localhost)
- `POSTGRES_PORT` (default: 5432)
- `POSTGRES_DB` (default: fraud_features)
- `POSTGRES_USER` (default: fraud_user)
- `POSTGRES_PASSWORD` (default: fraud_pass)
