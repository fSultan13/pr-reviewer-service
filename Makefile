.PHONY: format lint test check run migrate

format:
	poetry run isort .
	poetry run black .

lint:
	poetry run ruff check .

test:
	poetry run pytest -v

check: format lint test
	@echo "All checks passed!"

migrate:
	poetry run alembic upgrade head

run:
	poetry run uvicorn app.main:app --reload
