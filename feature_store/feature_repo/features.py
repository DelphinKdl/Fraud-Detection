"""Feast feature definitions for fraud detection."""
from datetime import timedelta

from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float64, Int64

# Entity: each transaction is identified by its index
transaction = Entity(
    name="transaction_id",
    join_keys=["transaction_id"],
    description="Unique transaction identifier",
)

# Offline source: parquet file with processed features
transaction_source = FileSource(
    path="data/processed/creditcard_features.parquet",
    timestamp_field="event_timestamp",
)

# Feature view: all 30 features used for fraud scoring
transaction_features = FeatureView(
    name="transaction_features",
    entities=[transaction],
    ttl=timedelta(days=1),
    schema=[
        Field(name="Time", dtype=Float64),
        Field(name="V1", dtype=Float64),
        Field(name="V2", dtype=Float64),
        Field(name="V3", dtype=Float64),
        Field(name="V4", dtype=Float64),
        Field(name="V5", dtype=Float64),
        Field(name="V6", dtype=Float64),
        Field(name="V7", dtype=Float64),
        Field(name="V8", dtype=Float64),
        Field(name="V9", dtype=Float64),
        Field(name="V10", dtype=Float64),
        Field(name="V11", dtype=Float64),
        Field(name="V12", dtype=Float64),
        Field(name="V13", dtype=Float64),
        Field(name="V14", dtype=Float64),
        Field(name="V15", dtype=Float64),
        Field(name="V16", dtype=Float64),
        Field(name="V17", dtype=Float64),
        Field(name="V18", dtype=Float64),
        Field(name="V19", dtype=Float64),
        Field(name="V20", dtype=Float64),
        Field(name="V21", dtype=Float64),
        Field(name="V22", dtype=Float64),
        Field(name="V23", dtype=Float64),
        Field(name="V24", dtype=Float64),
        Field(name="V25", dtype=Float64),
        Field(name="V26", dtype=Float64),
        Field(name="V27", dtype=Float64),
        Field(name="V28", dtype=Float64),
        Field(name="Amount", dtype=Float64),
    ],
    source=transaction_source,
    online=True,
)
