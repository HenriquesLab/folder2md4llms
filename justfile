# folder2md4llms - Development Commands
# Run 'just' or 'just --list' to see all available commands

# Settings
set shell := ["bash", "-uc"]

# Default recipe - show help
default:
    @just --list

# ===========================================================================
# SETUP
# ===========================================================================

# Install all dependencies and pre-commit hooks
setup:
    @echo "📦 Installing dependencies and setting up pre-commit hooks..."
    uv sync --dev
    uv run pre-commit install
    @echo "✅ Setup complete!"

# ===========================================================================
# DEVELOPMENT
# ===========================================================================

# Format code and fix lint issues
fix:
    @echo "🔧 Formatting code and fixing lint issues..."
    uv run ruff format src/ tests/
    uv run ruff check --fix src/ tests/
    @echo "✅ Fix complete."

# Run all static analysis checks
check:
    @echo "🔍 Running all static analysis checks..."
    uv run ruff check src/ tests/
    uv run ruff format --check src/ tests/
    uv run mypy src/
    uv run bandit -r src/ -ll
    @echo "✅ All checks passed."

# Run the test suite (accepts additional args: just test --verbose)
test +ARGS="":
    @echo "🧪 Running tests..."
    uv run pytest tests/ --cov=folder2md4llms --cov-report=term-missing {{ARGS}}
    @echo "✅ Tests finished."

# Run the folder2md4llms application (usage: just run --help)
run +ARGS="":
    @echo "🚀 Running the folder2md4llms application..."
    uv run folder2md {{ARGS}}

# ===========================================================================
# DISTRIBUTION
# ===========================================================================

# Check release readiness (changelog, version, tags)
check-release:
    #!/usr/bin/env python3
    import sys
    import subprocess
    import re

    print("🔍 Checking release readiness...")

    # Get current version
    result = subprocess.run(
        ["uv", "run", "python", "-c",
         "from folder2md4llms.__version__ import __version__; print(__version__)"],
        capture_output=True, text=True
    )
    version = result.stdout.strip()

    print(f"Current version: {version}")

    # Check CHANGELOG entry exists
    with open("CHANGELOG.md") as f:
        changelog = f.read()

    if f"## [{version}]" not in changelog:
        print(f"❌ No CHANGELOG entry found for version {version}")
        print(f"Please add an entry with format: ## [{version}] - YYYY-MM-DD")
        sys.exit(1)

    # Check CHANGELOG has proper date format
    date_pattern = r"\d{4}-\d{2}-\d{2}"
    version_pattern = f"## \\[{re.escape(version)}\\] - {date_pattern}"
    if not re.search(version_pattern, changelog):
        print("⚠️  WARNING: CHANGELOG entry may be missing date")
        print(f"Expected format: ## [{version}] - YYYY-MM-DD")

    # Check if version already tagged
    result = subprocess.run(
        ["git", "rev-parse", f"v{version}"],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        print(f"❌ Version {version} has already been tagged")
        print("Did you forget to bump the version?")
        sys.exit(1)

    print(f"✅ Release checks passed for version {version}")

# Build the sdist and wheel
build:
    @echo "📦 Building the sdist and wheel..."
    uv build
    @echo "✅ Build complete."

# Publish to TestPyPI
publish-test: build
    @echo "📦 Publishing to TestPyPI..."
    uv run twine upload --repository testpypi dist/*
    @echo "✅ Published to TestPyPI."

# Publish to PyPI
publish: build
    @echo "📦 Publishing to PyPI..."
    uv run twine upload dist/*
    @echo "✅ Published to PyPI."

# ===========================================================================
# UTILITIES
# ===========================================================================

# Clean build artifacts, caches, and temporary files
clean:
    @echo "🧹 Cleaning build artifacts, caches, and temporary files..."
    rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/ .ruff_cache/
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    uv cache clean
    @echo "✅ Clean complete."

# Show current version or provide bump instructions
version BUMP="":
    #!/usr/bin/env python3
    import subprocess

    bump = "{{BUMP}}"

    if not bump:
        # Show current version
        print("📋 Current version:")
        result = subprocess.run(
            ["uv", "run", "python", "-c",
             "from folder2md4llms.__version__ import __version__; print(__version__)"],
            capture_output=True, text=True
        )
        print(result.stdout.strip())
    else:
        print("📈 Version bumping not supported with current setup.")
        print("Please update src/folder2md4llms/__version__.py manually.")

# Generate API documentation
docs:
    @echo "📚 Generating API documentation..."
    uv run lazydocs \
        --output-path="./docs/api/" \
        --overview-file="README.md" \
        --src-base-url="https://github.com/henriqueslab/folder2md4llms/blob/main/" \
        --no-watermark \
        src/folder2md4llms
    @echo "📖 Documentation generated in docs/api/"
