.PHONY: pipeline train evaluate serve test lint clean install

# ── Setup ─────────────────────────────────────────────────────────────────────
install:
	pip install -r requirements-dev.txt

# ── ML Pipeline ───────────────────────────────────────────────────────────────
pipeline: ingest preprocess features train evaluate
	@echo "✅ Full pipeline complete."

ingest:
	python -m model.src.data.ingest

preprocess:
	python -m model.src.data.preprocess

features:
	python -m model.src.features.engineering

train:
	python -m model.src.models.train

evaluate:
	python -m model.src.evaluation.evaluate

# ── API ───────────────────────────────────────────────────────────────────────
serve:
	uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# ── Quality ───────────────────────────────────────────────────────────────────
test:
	pytest

lint:
	ruff check .
	mypy model/src backend/app

format:
	ruff format .

# ── Clean ─────────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf model/artifacts/*.pkl model/artifacts/*.joblib
	@echo "🧹 Cleaned."
