.PHONY: help dev dev-build dev-backend dev-frontend prod prod-build migrate lint test clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Dev ─────────────────────────────────────────────────────────────────────

dev: ## Start all services in dev mode (build + hot-reload via --watch rebuild)
	docker compose up --build --watch

dev-build: ## Build and start all services in dev mode
	docker compose up --build

dev-backend: ## Run backend locally (outside Docker, with uv)
	cd backend && uv run uvicorn app.main:app --reload --port 8000

dev-frontend: ## Run frontend locally (outside Docker, with pnpm)
	cd frontend && pnpm dev

dev-db: ## Start only the Postgres/pgvector database
	docker compose up db -d

# ─── Prod ────────────────────────────────────────────────────────────────────

prod: ## Build production images
	docker compose -f docker-compose.prod.yml build

prod-up: ## Start production services
	docker compose -f docker-compose.prod.yml up -d

prod-down: ## Stop production services
	docker compose -f docker-compose.prod.yml down

# ─── Database ─────────────────────────────────────────────────────────────────

migrate: ## Run Alembic migrations (expects DATABASE_URL in env)
	cd backend && uv run alembic upgrade head

migrate-new: ## Create a new Alembic migration
	cd backend && uv run alembic revision --autogenerate -m "$(name)"

migrate-rollback: ## Rollback last migration
	cd backend && uv run alembic downgrade -1

# ─── Quality ──────────────────────────────────────────────────────────────────

lint: ## Run ruff linter on backend, tsc on frontend
	cd backend && uv run ruff check .
	cd frontend && pnpm typecheck

test: ## Run backend tests
	cd backend && uv run pytest -v

test-unit: ## Run backend unit tests only (no external services)
	cd backend && uv run pytest -v -m "not integration"

# ─── Housekeeping ─────────────────────────────────────────────────────────────

clean: ## Remove venv, node_modules, caches
	rm -rf backend/.venv backend/__pycache__ backend/.pytest_cache
	rm -rf frontend/node_modules frontend/dist
