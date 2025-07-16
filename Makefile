# Centralized Makefile for folder2md4llms project
# All development commands are centralized here for consistency

.PHONY: help install dev clean clean-all test test-cov test-html test-watch lint format format-check type-check check fix docs docs-serve install-hooks pre-commit update-hooks build build-check publish-test setup-pypi-test publish version version-patch version-minor version-major version-set env-show env-create env-clean run run-help run-version run-current setup pre-commit-full release-patch release-minor release-major ci

# Default target
all: install dev

# ============================================================================
# PROJECT SETUP
# ============================================================================

# Install project dependencies
install:
	@echo "📦 Installing project dependencies..."
	uv sync

# Install development dependencies and set up development environment
dev:
	@echo "🔧 Setting up development environment..."
	uv sync --dev
	@echo "✅ Development environment ready!"

# Clean all build artifacts and cache files
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	@echo "✅ Clean complete!"

# Deep clean including environments
clean-all: clean
	@echo "🧹 Deep cleaning including environments..."
	uv run hatch env prune
	@echo "✅ Deep clean complete!"

# ============================================================================
# TESTING
# ============================================================================

# Run tests
test:
	@echo "🧪 Running tests..."
	uv run hatch run test

# Run tests with coverage report
test-cov:
	@echo "🧪 Running tests with coverage..."
	uv run hatch run test-cov

# Run tests with HTML coverage report
test-html:
	@echo "🧪 Running tests with HTML coverage..."
	uv run hatch -e dev run cov-html
	@echo "📊 Coverage report generated in htmlcov/"

# Run tests in watch mode (if available)
test-watch:
	@echo "🧪 Running tests in watch mode..."
	uv run hatch run test -- --lf

# ============================================================================
# CODE QUALITY
# ============================================================================

# Run linting checks only
lint:
	@echo "🔍 Running linting checks..."
	uv run hatch fmt --check

# Run code formatting
format:
	@echo "🎨 Formatting code..."
	uv run hatch fmt

# Check formatting without making changes
format-check:
	@echo "🎨 Checking code formatting..."
	uv run hatch fmt --check

# Run type checking
type-check:
	@echo "🔍 Running type checks..."
	uv run hatch -e dev run type-check

# Run all quality checks (lint, format, type, test)
check:
	@echo "🔍 Running all quality checks..."
	uv run hatch -e dev run check

# Fix all automatically fixable issues
fix:
	@echo "🔧 Fixing automatically fixable issues..."
	uv run hatch fmt

# ============================================================================
# DOCUMENTATION
# ============================================================================

# Generate documentation
docs:
	@echo "📚 Generating documentation..."
	uv run hatch -e dev run lazydocs --output-path docs/ --src-base-url "https://github.com/henriqueslab/folder2md4llms/blob/main/" src/folder2md4llms/
	@echo "📖 Documentation generated in docs/"

# Serve documentation locally (if available)
docs-serve:
	@echo "📚 Serving documentation locally..."
	@echo "💡 Open http://localhost:8000 to view documentation"
	python -m http.server 8000 --directory docs/

# ============================================================================
# PRE-COMMIT HOOKS
# ============================================================================

# Install pre-commit hooks
install-hooks:
	@echo "🪝 Installing pre-commit hooks..."
	uv run hatch -e dev run install-hooks

# Run pre-commit on all files
pre-commit:
	@echo "🪝 Running pre-commit on all files..."
	uv run hatch -e dev run pre-commit-run

# Update pre-commit hooks
update-hooks:
	@echo "🪝 Updating pre-commit hooks..."
	uv run hatch -e dev run pre-commit-run --hook-stage manual

# ============================================================================
# BUILD AND PACKAGING
# ============================================================================

# Build package
build:
	@echo "📦 Building package..."
	uv run hatch build
	@echo "✅ Package built successfully!"

# Build and check package
build-check: build
	@echo "📦 Checking built package..."
	@echo "📋 Package contents:"
	@echo "  Wheel: $(shell ls dist/*.whl)"
	@echo "  Source: $(shell ls dist/*.tar.gz)"
	@echo "  Size: $(shell du -h dist/* | cut -f1)"
	@echo "✅ Package check complete!"

# Publish to test PyPI
publish-test:
	@echo "📦 Publishing to test PyPI..."
	uv run hatch publish --repo https://test.pypi.org/legacy/
	@echo "✅ Published to test PyPI!"
	@echo "📦 View at: https://test.pypi.org/project/folder2md4llms/"

# Setup PyPI Test with guided process
setup-pypi-test:
	@echo "🔧 Setting up PyPI Test publishing..."
	@./scripts/pypi_test_setup.sh

# Publish to PyPI
publish:
	@echo "📦 Publishing to PyPI..."
	uv run hatch publish
	@echo "✅ Published to PyPI!"

# ============================================================================
# VERSION MANAGEMENT
# ============================================================================

# Show current version
version:
	@echo "📋 Current version:"
	uv run hatch version

# Bump patch version (0.1.0 -> 0.1.1)
version-patch:
	@echo "📈 Bumping patch version..."
	uv run hatch version patch
	@echo "✅ Version bumped!"

# Bump minor version (0.1.0 -> 0.2.0)
version-minor:
	@echo "📈 Bumping minor version..."
	uv run hatch version minor
	@echo "✅ Version bumped!"

# Bump major version (0.1.0 -> 1.0.0)
version-major:
	@echo "📈 Bumping major version..."
	uv run hatch version major
	@echo "✅ Version bumped!"

# Set specific version
version-set:
	@echo "📋 Current version: $(shell uv run hatch version)"
	@read -p "Enter new version: " version; uv run hatch version $$version
	@echo "✅ Version set!"

# ============================================================================
# ENVIRONMENT MANAGEMENT
# ============================================================================

# Show all hatch environments
env-show:
	@echo "🌍 Available environments:"
	uv run hatch env show

# Create/update all environments
env-create:
	@echo "🌍 Creating/updating environments..."
	uv run hatch env create
	@echo "✅ Environments ready!"

# Remove all environments
env-clean:
	@echo "🌍 Cleaning environments..."
	uv run hatch env prune
	@echo "✅ Environments cleaned!"

# ============================================================================
# APPLICATION COMMANDS
# ============================================================================

# Run the CLI application
run:
	@echo "🚀 Running folder2md CLI..."
	uv run folder2md

# Run CLI with help
run-help:
	@echo "🚀 Running folder2md CLI help..."
	uv run folder2md --help

# Run CLI with version
run-version:
	@echo "🚀 Running folder2md CLI version..."
	uv run folder2md --version

# Run CLI on current directory
run-current:
	@echo "🚀 Running folder2md on current directory..."
	uv run folder2md .

# ============================================================================
# DEVELOPMENT WORKFLOWS
# ============================================================================

# Complete development setup
setup: install dev install-hooks
	@echo "🎉 Development setup complete!"
	@echo "📝 Available commands:"
	@$(MAKE) help

# Pre-commit workflow
pre-commit-full: format lint type-check test
	@echo "✅ Pre-commit workflow complete!"

# Release workflow
release-patch: check version-patch build
	@echo "🚀 Patch release workflow complete!"

# Release workflow (minor)
release-minor: check version-minor build
	@echo "🚀 Minor release workflow complete!"

# Release workflow (major)
release-major: check version-major build
	@echo "🚀 Major release workflow complete!"

# CI workflow simulation
ci: install dev check build
	@echo "🤖 CI workflow simulation complete!"

# ============================================================================
# HELP AND INFORMATION
# ============================================================================

# Show help information
help:
	@echo "🛠️  folder2md4llms - Development Commands"
	@echo "════════════════════════════════════════════════════════════════"
	@echo ""
	@echo "📦 PROJECT SETUP:"
	@echo "  make install      - Install project dependencies"
	@echo "  make dev          - Set up development environment"
	@echo "  make setup        - Complete development setup"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make clean-all    - Deep clean including environments"
	@echo ""
	@echo "🧪 TESTING:"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make test-html    - Run tests with HTML coverage"
	@echo "  make test-watch   - Run tests in watch mode"
	@echo ""
	@echo "🔍 CODE QUALITY:"
	@echo "  make lint         - Run linting checks"
	@echo "  make format       - Format code"
	@echo "  make format-check - Check formatting"
	@echo "  make type-check   - Run type checking"
	@echo "  make check        - Run all quality checks"
	@echo "  make fix          - Fix automatically fixable issues"
	@echo ""
	@echo "📚 DOCUMENTATION:"
	@echo "  make docs         - Generate documentation"
	@echo "  make docs-serve   - Serve documentation locally"
	@echo ""
	@echo "🪝 PRE-COMMIT:"
	@echo "  make install-hooks - Install pre-commit hooks"
	@echo "  make pre-commit    - Run pre-commit checks"
	@echo "  make update-hooks  - Update pre-commit hooks"
	@echo ""
	@echo "📦 BUILD & PACKAGING:"
	@echo "  make build        - Build package"
	@echo "  make build-check  - Build and check package"
	@echo "  make setup-pypi-test - Setup PyPI Test publishing"
	@echo "  make publish-test - Publish to test PyPI"
	@echo "  make publish      - Publish to PyPI"
	@echo ""
	@echo "📋 VERSION MANAGEMENT:"
	@echo "  make version      - Show current version"
	@echo "  make version-patch - Bump patch version"
	@echo "  make version-minor - Bump minor version"
	@echo "  make version-major - Bump major version"
	@echo "  make version-set   - Set specific version"
	@echo ""
	@echo "🌍 ENVIRONMENT:"
	@echo "  make env-show     - Show environments"
	@echo "  make env-create   - Create/update environments"
	@echo "  make env-clean    - Clean environments"
	@echo ""
	@echo "🚀 APPLICATION:"
	@echo "  make run          - Run CLI"
	@echo "  make run-help     - Show CLI help"
	@echo "  make run-version  - Show CLI version"
	@echo "  make run-current  - Run on current directory"
	@echo ""
	@echo "🔄 WORKFLOWS:"
	@echo "  make pre-commit-full - Complete pre-commit workflow"
	@echo "  make release-patch   - Patch release workflow"
	@echo "  make release-minor   - Minor release workflow"
	@echo "  make release-major   - Major release workflow"
	@echo "  make ci             - CI workflow simulation"
	@echo ""
	@echo "For more information, visit: https://github.com/henriqueslab/folder2md4llms"
