.PHONY: train serve dashboard test docker-build docker-up docker-down lint clean

# --- Local commands ---

train:
	python -m src.pipeline --config config/config.yaml

serve:
	uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

dashboard:
	streamlit run dashboard/app.py --server.port 8501

test:
	python -m pytest tests/ -v

lint:
	python -m flake8 src/ --max-line-length 120
	python -m mypy src/ --ignore-missing-imports

# --- Docker commands ---

docker-build:
	docker build -t fraud-detection .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

# --- Cleanup ---

clean:
	rm -rf outputs/*.cbm outputs/metrics.json catboost_info/ __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
