.DEFAULT_GOAL := help

.PHONY: help install dev dev-backend dev-frontend lint format format-check typecheck test build audit check clean

help: ## Show this help menu
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install backend and frontend dependencies
	cd backend && uv sync --all-groups
	cd frontend && npm install

dev-backend: ## Run FastAPI backend development server
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run Vite React development server
	cd frontend && npm run dev

dev: ## Display instructions for concurrent local development
	@echo "To run full-stack dev:"
	@echo "  Terminal 1: make dev-backend"
	@echo "  Terminal 2: make dev-frontend"

lint: ## Run linters (Ruff for backend, ESLint for frontend)
	cd backend && uv run ruff check .
	cd frontend && npm run lint

format: ## Format codebases (Ruff for backend, Prettier for frontend)
	cd backend && uv run ruff format .
	cd frontend && npx prettier --write "src/**/*.{ts,tsx,css,json}"

format-check: ## Check formatting without changing files
	cd backend && uv run ruff format --check .
	cd frontend && npx prettier --check "src/**/*.{ts,tsx,css,json}"

typecheck: ## Run static type checkers (mypy for backend, tsc for frontend)
	cd backend && uv run mypy app/
	cd frontend && npx tsc --noEmit

test: ## Run test suites (pytest for backend, vitest for frontend)
	cd backend && uv run pytest --cov=app tests/
	cd frontend && npm test

build: ## Build production artifacts
	cd frontend && npm run build

audit: ## Run security vulnerability audits
	cd backend && uv run pip-audit
	cd frontend && npm audit --audit-level=high

check: lint format-check typecheck test build ## Run full quality gate
	@echo "\033[32m✔ All quality gates passed successfully!\033[0m"

clean: ## Remove temporary build caches and test artifacts
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/.mypy_cache backend/htmlcov backend/.coverage
	rm -rf frontend/dist frontend/node_modules/.vite
