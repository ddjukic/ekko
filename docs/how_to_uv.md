# uv: Modern Python Package Management for ekko

## Quick Reference

This guide covers essential uv commands and configuration for the ekko project.

## Installation

```bash
# Install uv (choose one method)
curl -LsSf https://astral.sh/uv/install.sh | sh
# or
pip install uv
# or
pipx install uv
```

## Setting Up Python 3.13

```bash
# Install Python 3.13
uv python install 3.13

# Pin Python version for project
uv python pin 3.13
```

## Project Structure

### pyproject.toml Configuration

```toml
[project]
name = "ekko"
version = "0.2.0"
description = "AI-powered podcast discovery, transcription and summarization"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "streamlit>=1.31.0",
    "streamlit-authenticator>=0.3.1",
    "openai>=1.12.0",
    "crewai>=0.30.0",
    "pydantic>=2.6.0",
    "python-dotenv>=1.0.0",
    "feedparser>=6.0.10",
    "requests>=2.31.0",
    "pandas>=2.2.0",
    "sqlalchemy>=2.0.25",
    "torch>=2.2.0",
    "transformers>=4.38.0",
    "langchain>=0.1.6",
    "langchain-community>=0.0.20",
    "langchain-openai>=0.0.5",
    "chromadb>=0.4.22",
    "tiktoken>=0.5.2",
    "readtime>=3.0.0",
    "youtube-transcript-api>=0.6.2",
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "pyngrok>=7.0.5",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.2.0",
    "mypy>=1.8.0",
    "pre-commit>=3.6.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "ipykernel>=6.29.0",
    "jupyter>=1.0.0",
]

[tool.ruff]
line-length = 88
target-version = "py313"
select = ["E", "F", "I", "N", "UP", "S", "B", "A", "C4", "T10", "SIM"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## Essential Commands

### Environment Management

```bash
# Create virtual environment
uv venv

# Sync dependencies from pyproject.toml
uv sync

# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Remove a dependency
uv remove package-name

# Update all dependencies
uv lock --upgrade
```

### Running Python Scripts

```bash
# Run any Python script (ALWAYS use this)
uv run python script.py

# Run Streamlit app
uv run streamlit run ekko_prototype/landing.py

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run ruff format .
```

## Docker Integration

### Optimized Dockerfile for uv

```dockerfile
FROM python:3.13-slim as builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies first (better caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Copy application code
COPY . .
RUN uv sync --frozen

# Production stage
FROM python:3.13-slim

# Copy virtual environment and app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

WORKDIR /app

# Set Python path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

# Run application
CMD ["python", "-m", "streamlit", "run", "ekko_prototype/landing.py", "--server.port=8080"]
```

## Workflow Best Practices

### 1. Always Use uv run
```bash
# ❌ Don't do this
python script.py
pip install package

# ✅ Do this
uv run python script.py
uv add package
```

### 2. Lock Dependencies
```bash
# After adding dependencies
uv lock

# Commit both pyproject.toml and uv.lock
git add pyproject.toml uv.lock
git commit -m "chore(deps): update project dependencies"
```

### 3. Development Setup
```bash
# Clone repository
git clone <repo>
cd ekko

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Set up environment
uv python install 3.13
uv sync --dev

# Run pre-commit hooks
uv run pre-commit install
```

## Performance Tips

1. **Use --frozen flag in CI/CD**: `uv sync --frozen` ensures reproducible builds
2. **Enable bytecode compilation**: Set `UV_COMPILE_BYTECODE=1` for faster startup
3. **Cache virtual environments**: In Docker, cache the `.venv` directory
4. **Use lock files**: Always commit `uv.lock` for reproducible installs

## Troubleshooting

### Common Issues

1. **Python version not found**
   ```bash
   uv python install 3.13
   uv python pin 3.13
   ```

2. **Dependencies not installing**
   ```bash
   uv sync --reinstall
   ```

3. **Import errors**
   ```bash
   # Always use uv run
   uv run python your_script.py
   ```

## Migration from pip/requirements.txt

```bash
# Convert requirements.txt to pyproject.toml
uv add $(cat requirements.txt | tr '\n' ' ')

# Or manually add each dependency
uv add streamlit openai crewai ...
```

## Key Environment Variables

```bash
# For production Docker builds
UV_COMPILE_BYTECODE=1
UV_LINK_MODE=copy
UV_PYTHON_DOWNLOADS=never

# For faster local development
UV_CACHE_DIR=~/.cache/uv
```

Remember: **ALWAYS use `uv run` for executing Python scripts and commands!**