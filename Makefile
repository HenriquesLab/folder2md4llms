# Simplified Makefile for folder2md4llms
# Targets are grouped into logical workflows for a better developer experience.

.PHONY: help setup fix check test run build publish-test publish clean version docs

# ===========================================================================
# HELP
# =================================0==========================================

help:
	@echo "🛠️  folder2md4llms - Development Commands"
	@echo "════════════════════════════════════════════════════════════════"
	@echo ""
	@echo "  Targets:"
	@echo "    make help           - Shows this help message."
	@echo ""
	@echo "  Setup:"
	@echo "    make setup          - Installs all dependencies and pre-commit hooks."
	@echo ""
	@echo "  Development:"
	@echo "    make fix            - Formats code and fixes lint issues."
	@echo "    make check          - Runs all static analysis (format check, lint, types)."
	@echo "    make test           - Runs the test suite. Accepts 'ARGS' for variations (e.g., make test ARGS=\"--cov-report=html\")."
	@echo "    make run            - Executes the CLI application. Accepts 'ARGS' (e.g., make run ARGS=\"--help\")."
	@echo ""
	@echo "  Distribution:"
	@echo "    make build          - Builds the sdist and wheel."
	@echo "    make publish-test   - Publishes to TestPyPI."
	@echo "    make publish        - Publishes to PyPI."
	@echo ""
	@echo "  Utilities:"
	@echo "    make clean          - Removes all build artifacts and caches."
	@echo "    make version        - Shows or bumps the project version. Accepts 'BUMP=<level>' (e.g., make version BUMP=patch)."
	@echo "    make docs           - Generates API documentation."
	@echo ""
	@echo "For more information, visit: https://github.com/henriqueslab/folder2md4llms"


# ===========================================================================
# SETUP
# =================================0==========================================

setup:
	@echo "📦 Installing dependencies and setting up pre-commit hooks..."
	uv sync --dev
	uv run pre-commit install
	@echo "✅ Setup complete!"

# ===========================================================================
# DEVELOPMENT
# =================================0==========================================

fix:
	@echo "🔧 Formatting code and fixing lint issues..."
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/
	@echo "✅ Fix complete."

check:
	@echo "🔍 Running all static analysis checks..."
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/
	uv run mypy src/
	uv run bandit -r src/ -ll
	@echo "✅ All checks passed."

test:
	@echo "🧪 Running tests..."
	uv run pytest tests/ --cov=folder2md4llms --cov-report=term-missing $(ARGS)
	@echo "✅ Tests finished."

run:
	@echo "🚀 Running the folder2md4llms application..."
	uv run folder2md $(ARGS)

# ===========================================================================
# DISTRIBUTION
# =================================0==========================================

build:
	@echo "📦 Building the sdist and wheel..."
	rye build
	@echo "✅ Build complete."

publish-test: build
	@echo "📦 Publishing to TestPyPI..."
	uv run twine upload --repository testpypi dist/*
	@echo "✅ Published to TestPyPI."

publish: build
	@echo "📦 Publishing to PyPI..."
	uv run twine upload dist/*
	@echo "✅ Published to PyPI."

# ===========================================================================
# UTILITIES
# =================================0==========================================

clean:
	@echo "🧹 Cleaning build artifacts, caches, and temporary files..."
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	# Clean UV cache
	uv cache clean
	@echo "✅ Clean complete."

version:
ifeq ($(BUMP),)
	@echo "📋 Current version:"
	@rye version
else
	@echo "📈 Bumping $(BUMP) version..."
	@rye version --bump $(BUMP)
	@echo "✅ Version bumped to: $(shell rye version)"
endif

docs:
	@echo "📚 Generating API documentation..."
	uv run lazydocs \
		--output-path="./docs/api/" \
		--overview-file="README.md" \
		--src-base-url="https://github.com/henriqueslab/folder2md4llms/blob/main/" \
		--no-watermark \
		src/folder2md4llms
	@echo "📖 Documentation generated in docs/api/"

.DEFAULT_GOAL := help
