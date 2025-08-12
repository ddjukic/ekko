# ekko Development Makefile

.PHONY: help install dev-install run test lint format clean docker-build docker-run

# Variables
PYTHON_VERSION := 3.13
PROJECT_NAME := ekko
DOCKER_IMAGE := $(PROJECT_NAME):latest
DOCKER_REGISTRY := gcr.io/$(GCP_PROJECT_ID)/$(PROJECT_NAME)

# Default target
help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install production dependencies with uv
	@echo "Installing Python $(PYTHON_VERSION)..."
	uv python install $(PYTHON_VERSION)
	uv python pin $(PYTHON_VERSION)
	@echo "Installing production dependencies..."
	uv sync --frozen

dev-install: ## Install all dependencies including dev tools
	@echo "Installing Python $(PYTHON_VERSION)..."
	uv python install $(PYTHON_VERSION)
	uv python pin $(PYTHON_VERSION)
	@echo "Installing all dependencies..."
	uv sync --all-extras
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install

run: ## Run the Streamlit application
	uv run streamlit run ekko_prototype/landing.py

run-transcriber: ## Run the transcription server
	cd ekko_prototype/pages/tools && uv run python transcriber_server.py

test: ## Run tests with pytest
	uv run pytest tests/ -v --cov

test-coverage: ## Run tests with coverage report
	uv run pytest tests/ -v --cov --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

lint: ## Run linting with ruff
	uv run ruff check .
	uv run mypy ekko_prototype rss_parser

format: ## Format code with ruff
	uv run ruff format .
	uv run ruff check --fix .

clean: ## Clean up temporary files and caches
	@echo "Cleaning Python cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "Cleaning test and coverage files..."
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

docker-build: ## Build Docker image
	docker build -t $(DOCKER_IMAGE) .

docker-run: ## Run Docker container locally
	docker run -p 8080:8080 \
		--env-file .env \
		$(DOCKER_IMAGE)

docker-push: ## Push Docker image to registry
	docker tag $(DOCKER_IMAGE) $(DOCKER_REGISTRY)
	docker push $(DOCKER_REGISTRY)

migrate-from-requirements: ## Migrate from requirements.txt to pyproject.toml
	@echo "Converting requirements.txt to uv dependencies..."
	@if [ -f requirements.txt ]; then \
		cat requirements.txt | xargs -I {} uv add {}; \
	else \
		echo "requirements.txt not found"; \
	fi

setup-gcp: ## Set up Google Cloud project
	gcloud config set project $(GCP_PROJECT_ID)
	gcloud auth configure-docker

deploy: docker-build docker-push ## Deploy to Google Cloud Run
	gcloud run deploy $(PROJECT_NAME) \
		--image $(DOCKER_REGISTRY) \
		--platform managed \
		--region $(GCP_REGION) \
		--allow-unauthenticated

pre-commit: ## Run pre-commit checks
	uv run pre-commit run --all-files

check: lint test ## Run all checks (lint and test)

dev: dev-install ## Set up development environment
	@echo "Development environment ready!"
	@echo "Run 'make run' to start the application"

.DEFAULT_GOAL := help