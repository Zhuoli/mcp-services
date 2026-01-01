# MCP Servers Makefile
# Main entrypoint for all project operations

.PHONY: help install install-dev sync clean \
        run-oracle run-atlassian run-repos \
        chatbot chatbot-repos chatbot-all \
        lint format typecheck test check \
        build

# Default target
help:
	@echo "MCP Servers - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install production dependencies"
	@echo "  make install-dev  Install with development dependencies"
	@echo "  make sync         Sync dependencies (after pyproject.toml changes)"
	@echo "  make clean        Remove build artifacts and caches"
	@echo ""
	@echo "Run Servers:"
	@echo "  make run-oracle     Run Oracle Cloud MCP server"
	@echo "  make run-atlassian  Run Atlassian MCP server"
	@echo "  make run-repos      Run Code Repos MCP server"
	@echo ""
	@echo "Examples:"
	@echo "  make chatbot        Run chatbot with repos server (default)"
	@echo "  make chatbot-repos  Run chatbot with repos server"
	@echo "  make chatbot-all    Run chatbot with all servers"
	@echo ""
	@echo "Development:"
	@echo "  make lint       Run linter (ruff)"
	@echo "  make format     Format code (ruff)"
	@echo "  make typecheck  Run type checker (mypy)"
	@echo "  make test       Run tests (pytest)"
	@echo "  make check      Run all checks (lint + typecheck + test)"
	@echo ""
	@echo "Build:"
	@echo "  make build      Build package"

# =============================================================================
# Setup
# =============================================================================

install:
	uv sync --no-dev

install-dev:
	uv sync

sync:
	uv sync

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# =============================================================================
# Run Servers
# =============================================================================

run-oracle:
	uv run python -m mcp_servers.oracle_cloud.server

run-atlassian:
	uv run python -m mcp_servers.atlassian.server

run-repos:
	uv run python -m mcp_servers.code_repos.server

# Aliases
oracle: run-oracle
atlassian: run-atlassian
repos: run-repos

# =============================================================================
# Development
# =============================================================================

lint:
	uv run ruff check src/

format:
	uv run ruff format src/
	uv run ruff check --fix src/

typecheck:
	uv run mypy src/mcp_servers/

test:
	uv run pytest tests/ -v

check: lint typecheck test

# =============================================================================
# Build
# =============================================================================

build:
	uv build

# =============================================================================
# Convenience targets
# =============================================================================

# Run server with environment file loaded
run-oracle-env:
	@if [ -f .env ]; then \
		set -a && source .env && set +a && uv run python -m mcp_servers.oracle_cloud.server; \
	else \
		echo "Error: .env file not found. Copy .env.example to .env first."; \
		exit 1; \
	fi

run-atlassian-env:
	@if [ -f .env ]; then \
		set -a && source .env && set +a && uv run python -m mcp_servers.atlassian.server; \
	else \
		echo "Error: .env file not found. Copy .env.example to .env first."; \
		exit 1; \
	fi

run-repos-env:
	@if [ -f .env ]; then \
		set -a && source .env && set +a && uv run python -m mcp_servers.code_repos.server; \
	else \
		echo "Error: .env file not found. Copy .env.example to .env first."; \
		exit 1; \
	fi

# =============================================================================
# Examples
# =============================================================================

# Run chatbot with repos server (default, no extra config needed)
chatbot: chatbot-repos

chatbot-repos:
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "Error: ANTHROPIC_API_KEY environment variable not set"; \
		echo "Get your API key from: https://console.anthropic.com/"; \
		exit 1; \
	fi
	cd src && uv run python -m examples.chatbot --servers repos

# Run chatbot with all servers (requires all env vars configured)
chatbot-all:
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "Error: ANTHROPIC_API_KEY environment variable not set"; \
		exit 1; \
	fi
	@if [ -f .env ]; then \
		set -a && source .env && set +a && cd src && uv run python -m examples.chatbot --servers repos,oracle,atlassian; \
	else \
		echo "Error: .env file not found. Copy .env.example to .env first."; \
		exit 1; \
	fi

# Run chatbot with specific servers
chatbot-atlassian:
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "Error: ANTHROPIC_API_KEY environment variable not set"; \
		exit 1; \
	fi
	@if [ -f .env ]; then \
		set -a && source .env && set +a && cd src && uv run python -m examples.chatbot --servers repos,atlassian; \
	else \
		cd src && uv run python -m examples.chatbot --servers repos,atlassian; \
	fi
