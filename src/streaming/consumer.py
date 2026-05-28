"""Kafka consumer simulator for real-time fraud scoring.

Simulates a Kafka-style event-driven architecture using asyncio queues.
No actual Kafka broker required — demonstrates the pattern for production systems.

Usage:
    python -m src.streaming.consumer --config config/config.yaml
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier

from src.config import load_config

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]


class FraudScoringConsumer:
    """Simulates a Kafka consumer that scores transactions in real time."""

    def __init__(self, model_path: str, threshold: float = 0.5):
        self.model = CatBoostClassifier()
        self.model.load_model(model_path)
        self.threshold = threshold
        self.queue: asyncio.Queue = asyncio.Queue()
        self.results: list[dict] = []
        self._running = False

    async def produce(self, transactions: pd.DataFrame) -> None:
        """Simulate Kafka producer — push transactions to the queue."""
        for idx, row in transactions.iterrows():
            event = {
                "transaction_id": int(idx),
                "timestamp": time.time(),
                "features": row[FEATURE_COLUMNS].to_dict(),
            }
            await self.queue.put(event)
            await asyncio.sleep(0.01)  # Simulate real-time stream delay

        # Sentinel to signal end of stream
        await self.queue.put(None)
        logger.info("Producer: pushed %d transactions to queue", len(transactions))

    async def consume(self) -> None:
        """Simulate Kafka consumer — score transactions from the queue."""
        self._running = True
        processed = 0

        while self._running:
            event = await self.queue.get()

            if event is None:
                self._running = False
                break

            start = time.time()
            features = pd.DataFrame([event["features"]])[FEATURE_COLUMNS]
            proba = float(self.model.predict_proba(features)[0][1])
            pred = int(proba >= self.threshold)
            latency_ms = (time.time() - start) * 1000

            action = "HOLD" if pred == 1 else "PASS"
            result = {
                "transaction_id": event["transaction_id"],
                "fraud_probability": round(proba, 6),
                "prediction": pred,
                "action": action,
                "latency_ms": round(latency_ms, 2),
            }
            self.results.append(result)
            processed += 1

            if pred == 1:
                logger.warning(
                    "🚨 FRAUD DETECTED | txn_id=%d | prob=%.4f | action=%s | latency=%.1fms",
                    event["transaction_id"], proba, action, latency_ms,
                )
            else:
                logger.info(
                    "✓ txn_id=%d | prob=%.4f | action=%s | latency=%.1fms",
                    event["transaction_id"], proba, action, latency_ms,
                )

        logger.info("Consumer: processed %d transactions", processed)

    async def run(self, transactions: pd.DataFrame) -> list[dict]:
        """Run producer and consumer concurrently."""
        logger.info("Starting streaming pipeline (%d transactions)", len(transactions))
        await asyncio.gather(
            self.produce(transactions),
            self.consume(),
        )
        return self.results

    def summary(self) -> dict:
        """Return summary statistics of the streaming run."""
        if not self.results:
            return {}
        fraud_count = sum(1 for r in self.results if r["prediction"] == 1)
        latencies = [r["latency_ms"] for r in self.results]
        return {
            "total_transactions": len(self.results),
            "fraud_detected": fraud_count,
            "legitimate": len(self.results) - fraud_count,
            "avg_latency_ms": round(np.mean(latencies), 2),
            "p95_latency_ms": round(np.percentile(latencies, 95), 2),
            "max_latency_ms": round(max(latencies), 2),
        }


async def main():
    """Run the streaming consumer simulator."""
    config = load_config("config/config.yaml")

    model_path = Path(config.outputs.model_dir) / f"catboost_model.{config.outputs.model_format}"
    if not model_path.exists():
        logger.error("Model not found: %s. Run pipeline first.", model_path)
        return

    # Load sample transactions for simulation
    data_path = Path(config.data.processed_path)
    if not data_path.exists():
        data_path = Path(config.data.raw_path)
    df = pd.read_parquet(data_path)

    sample_size = min(config.streaming.sample_size, len(df))
    sample = df.sample(n=sample_size, random_state=42)

    consumer = FraudScoringConsumer(
        model_path=str(model_path),
        threshold=config.streaming.score_threshold,
    )

    results = await consumer.run(sample)

    # Print summary
    summary = consumer.summary()
    logger.info("=== Streaming Summary ===")
    for key, value in summary.items():
        logger.info("  %s: %s", key, value)

    # Save results
    output_path = Path(config.outputs.model_dir) / "streaming_results.json"
    with open(output_path, "w") as f:
        json.dump({"summary": summary, "predictions": results}, f, indent=2)
    logger.info("Results saved to %s", output_path)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(main())
