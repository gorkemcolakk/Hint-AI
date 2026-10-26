.PHONY: up down build logs test lint format migrate eval client-gen client-test

up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f api

test:
	cd apps/api && pytest

lint:
	cd apps/api && ruff check . && ruff format --check . && mypy app

format:
	cd apps/api && ruff format . && ruff check --fix .

migrate:
	cd apps/api && alembic upgrade head

eval:
	@echo eval henüz yapılandırılmadı (M4+)

client-gen:
	@echo "client-gen henüz yapılandırılmadı (M1.5: openapi-typescript)"

client-test:
	@echo "client-test henüz yapılandırılmadı (M1.5: jest + tsc)"
