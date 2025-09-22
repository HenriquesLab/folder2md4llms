"""Nox configuration for folder2md4llms with UV optimization and environment reuse.

This configuration is designed to:
1. Use UV for all dependency management (10-100x faster than pip)
2. Maximize environment reuse to minimize disk space and setup time
3. Group sessions by dependency requirements for optimal sharing
4. Provide comprehensive testing across Python versions
5. Integrate seamlessly with existing Make workflow
"""

from pathlib import Path

import nox

# =============================================================================
# Configuration
# =============================================================================

# Use UV as the default backend for all sessions (much faster than pip)
nox.options.default_venv_backend = "uv"

# Enable environment reuse by default to minimize space and setup time
nox.options.reuse_existing_virtualenvs = True

# Supported Python versions (matches GitHub Actions matrix)
PYTHON_VERSIONS = ["3.11", "3.12", "3.13"]
LATEST_PYTHON = "3.13"

# Project paths
SRC_DIR = "src"
TESTS_DIR = "tests"
DOCS_DIR = "docs"

# =============================================================================
# Dependency Group Helpers
# =============================================================================


def install_base_deps(session):
    """Install base dependencies using UV sync for maximum speed."""
    session.log("📦 Installing base dependencies with UV...")
    session.run("uv", "sync", "--group", "dev", "--no-install-project")


def install_with_group(session, group):
    """Install dependencies for a specific group using UV."""
    session.log(f"📦 Installing {group} dependencies with UV...")
    session.run("uv", "sync", "--group", group)


def install_minimal_deps(session):
    """Install only minimal dependencies needed for basic functionality."""
    session.log("📦 Installing minimal dependencies...")
    session.run("uv", "sync", "--no-group", "dev")


def install_project_editable(session):
    """Install the project in editable mode."""
    session.run("uv", "pip", "install", "-e", ".")


# =============================================================================
# Core Testing Sessions (Shared Environment: test-base)
# =============================================================================


@nox.session(python=PYTHON_VERSIONS, reuse_venv=True)
def test(session):
    """Run the full test suite across Python versions.

    Environment: Shared across Python versions for efficiency.
    Dependencies: Core testing stack (pytest, coverage, etc.)

    Usage:
        nox -s test                    # All Python versions
        nox -s "test-3.11"            # Specific Python version
        nox -s test -- tests/test_security.py  # Specific test file
    """
    install_base_deps(session)
    install_project_editable(session)

    # Use pytest with coverage and parallel execution
    args = [
        "uv",
        "run",
        "pytest",
        "tests/",
        "--cov=folder2md4llms",
        "--cov-report=term-missing",
        "-n",
        "auto",  # Parallel execution
        "--maxfail=10",  # Stop after 10 failures
        "--tb=short",
    ]

    if session.posargs:
        args.extend(session.posargs)

    session.run(*args)


@nox.session(reuse_venv=True)
def test_minimal(session):
    """Test with minimal dependencies to ensure core functionality works.

    Environment: Minimal dependencies only.
    Purpose: Verify the package works without optional dependencies.
    """
    install_minimal_deps(session)
    install_project_editable(session)

    # Basic test run without optional features
    session.run(
        "uv",
        "run",
        "pytest",
        "tests/",
        "-k",
        "not (tiktoken or optional)",  # Skip tests requiring optional deps
        "--tb=short",
    )


@nox.session(reuse_venv=True)
def smoke(session):
    """Quick smoke tests for rapid feedback during development.

    Environment: Reuses test environment.
    Purpose: Fast validation of core functionality.
    """
    install_base_deps(session)
    install_project_editable(session)

    # Run only fast, essential tests
    session.run(
        "uv",
        "run",
        "pytest",
        "tests/test_security.py",  # Security is critical
        "tests/test_cli.py",  # CLI functionality
        "-v",
        "--tb=short",
    )


# =============================================================================
# Quality Assurance Sessions (Shared Environment: qa-base)
# =============================================================================


@nox.session(reuse_venv=True)
def lint(session):
    """Run ruff linting checks.

    Environment: Shared QA environment with all quality tools.
    Purpose: Code quality and style enforcement.
    """
    install_base_deps(session)

    session.log("🔍 Running ruff linting...")
    session.run("uv", "run", "ruff", "check", SRC_DIR, TESTS_DIR)


@nox.session(reuse_venv=True)
def format(session):
    """Format code with ruff.

    Environment: Reuses QA environment (ruff already installed).
    Purpose: Automatic code formatting.
    """
    install_base_deps(session)

    session.log("🎨 Formatting code with ruff...")
    session.run("uv", "run", "ruff", "format", SRC_DIR, TESTS_DIR)


@nox.session(reuse_venv=True)
def format_check(session):
    """Check if code is properly formatted.

    Environment: Reuses QA environment.
    Purpose: CI/CD formatting validation.
    """
    install_base_deps(session)

    session.log("✅ Checking code formatting...")
    session.run("uv", "run", "ruff", "format", "--check", SRC_DIR, TESTS_DIR)


@nox.session(reuse_venv=True)
def typing(session):
    """Run MyPy type checking.

    Environment: Reuses QA environment.
    Purpose: Static type analysis.
    """
    install_base_deps(session)

    session.log("🔍 Running MyPy type checking...")
    session.run("uv", "run", "mypy", SRC_DIR)


@nox.session(reuse_venv=True)
def security(session):
    """Run Bandit security scanning.

    Environment: Reuses QA environment.
    Purpose: Security vulnerability detection.
    """
    install_base_deps(session)

    session.log("🔒 Running Bandit security scanning...")
    session.run("uv", "run", "bandit", "-r", SRC_DIR, "-ll")


# =============================================================================
# Full Feature Testing (Shared Environment: full-base)
# =============================================================================


@nox.session(python=LATEST_PYTHON, reuse_venv=True)
def test_full(session):
    """Run tests with all optional dependencies enabled.

    Environment: Full feature environment with all optional dependencies.
    Purpose: Test complete functionality including optional features.
    """
    install_base_deps(session)
    install_with_group(session, "tiktoken")
    install_project_editable(session)

    session.log("🚀 Running full feature tests...")
    session.run(
        "uv",
        "run",
        "pytest",
        "tests/",
        "--cov=folder2md4llms",
        "--cov-report=html",  # Generate HTML coverage report
        "--cov-report=xml",  # For CI/CD coverage reporting
        "-n",
        "auto",
        "--maxfail=5",
    )


@nox.session(python=LATEST_PYTHON, reuse_venv=True)
def test_converters(session):
    """Focus testing on document converters.

    Environment: Reuses full-base environment.
    Purpose: Intensive testing of conversion functionality.
    """
    install_base_deps(session)
    install_project_editable(session)

    session.log("📄 Testing document converters...")
    session.run(
        "uv",
        "run",
        "pytest",
        "tests/test_converters.py",
        "tests/test_binary_distribution.py",
        "-v",
        "--tb=long",
    )


@nox.session(python=LATEST_PYTHON, reuse_venv=True)
def integration(session):
    """Run integration tests.

    Environment: Reuses full-base environment.
    Purpose: End-to-end testing of complete workflows.
    """
    install_base_deps(session)
    install_project_editable(session)

    session.log("🔗 Running integration tests...")
    session.run(
        "uv", "run", "pytest", "tests/", "-k", "integration", "-v", "--tb=short"
    )


# =============================================================================
# Build & Distribution (Shared Environment: build-base)
# =============================================================================


@nox.session(reuse_venv=True)
def build(session):
    """Build source and wheel distributions.

    Environment: Build environment with packaging tools.
    Purpose: Create distributable packages.
    """
    install_base_deps(session)
    install_with_group(session, "build")

    session.log("📦 Building distributions...")
    # Clean previous builds
    session.run("rm", "-rf", "dist/", "build/", external=True)
    session.run("uv", "build")


@nox.session(reuse_venv=True)
def install_test(session):
    """Test package installation in clean environment.

    Environment: Clean environment for installation testing.
    Purpose: Verify package installs correctly.
    """
    session.log("🧪 Testing package installation...")

    # Build first if not already built
    if not Path("dist").exists():
        session.run("uv", "build")

    # Find the wheel file
    wheel_files = list(Path("dist").glob("*.whl"))
    if not wheel_files:
        session.error("No wheel file found in dist/")

    wheel_file = wheel_files[0]

    # Install and test
    session.run("uv", "pip", "install", str(wheel_file))
    session.run("folder2md", "--version")
    session.run("folder2md", "--help")


# =============================================================================
# Documentation & Coverage
# =============================================================================


@nox.session(python=LATEST_PYTHON, reuse_venv=True)
def docs(session):
    """Generate API documentation.

    Environment: Documentation environment.
    Purpose: Create up-to-date API docs.
    """
    install_base_deps(session)

    session.log("📚 Generating documentation...")
    session.run(
        "uv",
        "run",
        "lazydocs",
        "--output-path",
        "./docs/api/",
        "--overview-file",
        "README.md",
        "--src-base-url",
        "https://github.com/henriqueslab/folder2md4llms/blob/main/",
        "--no-watermark",
        "src/folder2md4llms",
    )


@nox.session(python=LATEST_PYTHON, reuse_venv=True)
def coverage(session):
    """Generate comprehensive coverage report.

    Environment: Reuses test environment.
    Purpose: Detailed coverage analysis.
    """
    install_base_deps(session)
    install_project_editable(session)

    session.log("📊 Generating coverage report...")
    session.run(
        "uv",
        "run",
        "pytest",
        "tests/",
        "--cov=folder2md4llms",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "-n",
        "auto",
    )

    session.log("Coverage report generated in htmlcov/")


# =============================================================================
# Development Convenience Sessions
# =============================================================================


@nox.session(reuse_venv=True)
def dev(session):
    """Set up development environment with all dependencies.

    Environment: Complete development environment.
    Purpose: One-command development setup.
    """
    install_base_deps(session)
    install_with_group(session, "tiktoken")
    install_with_group(session, "build")
    install_project_editable(session)

    session.log("🛠️  Development environment ready!")
    session.log("💡 Run commands with: uv run <command>")
    session.log("💡 Or activate with: .nox/dev/bin/activate")


@nox.session(reuse_venv=True)
def fix(session):
    """Format code and fix linting issues.

    Environment: Reuses QA environment.
    Purpose: One-command code cleanup.
    """
    install_base_deps(session)

    session.log("🔧 Fixing code issues...")
    session.run("uv", "run", "ruff", "format", SRC_DIR, TESTS_DIR)
    session.run("uv", "run", "ruff", "check", "--fix", SRC_DIR, TESTS_DIR)


@nox.session(reuse_venv=True)
def check(session):
    """Run all quality checks (format, lint, typing, security).

    Environment: Reuses QA environment.
    Purpose: Comprehensive quality validation.
    """
    install_base_deps(session)

    session.log("🔍 Running all quality checks...")

    # Format check
    session.run("uv", "run", "ruff", "format", "--check", SRC_DIR, TESTS_DIR)

    # Linting
    session.run("uv", "run", "ruff", "check", SRC_DIR, TESTS_DIR)

    # Type checking
    session.run("uv", "run", "mypy", SRC_DIR)

    # Security scanning
    session.run("uv", "run", "bandit", "-r", SRC_DIR, "-ll")


# =============================================================================
# CI/CD Optimized Sessions
# =============================================================================


@nox.session(python=PYTHON_VERSIONS, reuse_venv=True)
def ci_test(session):
    """CI-optimized test session with XML output.

    Environment: Shared test environment.
    Purpose: CI/CD pipeline testing with proper reporting.
    """
    install_base_deps(session)
    install_project_editable(session)

    session.run(
        "uv",
        "run",
        "pytest",
        "tests/",
        "--cov=folder2md4llms",
        "--cov-report=xml",  # For CI coverage reporting
        "--cov-report=term-missing",
        "-n",
        "auto",
        "--maxfail=10",
        "--tb=short",
        "-v",
    )


@nox.session(reuse_venv=True)
def ci_quality(session):
    """CI-optimized quality checks with proper exit codes.

    Environment: Reuses QA environment.
    Purpose: CI/CD pipeline quality gates.
    """
    install_base_deps(session)

    # Run all checks, failing fast on any issue
    session.run("uv", "run", "ruff", "check", SRC_DIR, TESTS_DIR)
    session.run("uv", "run", "ruff", "format", "--check", SRC_DIR, TESTS_DIR)
    session.run("uv", "run", "mypy", SRC_DIR)
    session.run("uv", "run", "bandit", "-r", SRC_DIR, "-ll")


# =============================================================================
# Performance & Benchmarking
# =============================================================================


@nox.session(python=LATEST_PYTHON, reuse_venv=True)
def benchmark(session):
    """Run performance benchmarks.

    Environment: Full feature environment.
    Purpose: Performance regression testing.
    """
    install_base_deps(session)
    install_project_editable(session)

    session.log("⚡ Running performance benchmarks...")

    # Create a test directory structure for benchmarking
    test_repo = Path("benchmark_test_repo")
    if test_repo.exists():
        session.run("rm", "-rf", str(test_repo), external=True)

    # Simple benchmark - process this project
    session.run(
        "uv",
        "run",
        "python",
        "-c",
        """
import time
from folder2md4llms.processor import RepositoryProcessor
from folder2md4llms.utils.config import Config
from pathlib import Path

config = Config()
processor = RepositoryProcessor(config)

start = time.time()
result = processor.process(Path('.'))
end = time.time()

print(f'Processing took {end - start:.2f} seconds')
print(f'Output length: {len(result)} characters')
""",
    )


# =============================================================================
# Cleanup & Utilities
# =============================================================================


@nox.session
def clean(session):
    """Clean up all build artifacts and caches.

    Purpose: Reset project to clean state.
    """
    session.log("🧹 Cleaning up build artifacts...")

    # Clean build artifacts
    artifacts = [
        "build/",
        "dist/",
        "*.egg-info/",
        ".pytest_cache/",
        ".mypy_cache/",
        ".ruff_cache/",
        "htmlcov/",
        ".coverage",
        "coverage.xml",
        "__pycache__/",
        "*.pyc",
    ]

    for pattern in artifacts:
        session.run("rm", "-rf", pattern, external=True)

    session.log("✅ Cleanup complete!")


@nox.session
def list_envs(session):
    """List all nox environments and their sizes.

    Purpose: Environment management and debugging.
    """
    import subprocess  # nosec B404

    session.log("📋 Nox environments:")

    nox_dir = Path(".nox")
    if nox_dir.exists():
        result = subprocess.run(  # nosec B603, B607
            ["du", "-sh", *nox_dir.glob("*")], capture_output=True, text=True
        )
        if result.stdout:
            session.log("\n" + result.stdout)
    else:
        session.log("No nox environments found")


# =============================================================================
# Session Groups for Easy Execution
# =============================================================================

# Define session groups for easy parallel execution
nox.options.sessions = [
    "lint",
    "typing",
    "security",  # Quality checks (fast)
    "test",  # Core testing
]

# Additional groups can be run with:
# nox -s test-full integration     # Full testing
# nox -s build install_test        # Build verification
# nox -s fix check                 # Development workflow
