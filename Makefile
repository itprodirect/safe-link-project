.PHONY: install test lint typecheck format audit check clean

install:
	python -m venv .venv
	. .venv/bin/activate && pip install -e ".[dev]"

test:
	pytest -v --tb=short

test-cov:
	pytest -v --cov=lsh --cov-report=term-missing

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

typecheck:
	mypy src/

audit:
	pip-audit --progress-spinner off

# Run all checks (use before committing)
check: lint typecheck test

clean:
	rm -rf .venv __pycache__ .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
