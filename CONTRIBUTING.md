# Contributing to folder2md4llms

Thank you for your interest in contributing to folder2md4llms! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the problem
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, installation method)
- **Error messages** or logs if applicable

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description** of the feature
- **Use cases** - why this would be useful
- **Possible implementation** - if you have ideas
- **Examples** - mockups, code samples, etc.

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following our coding standards (see below)
3. **Add tests** if you're adding functionality
4. **Update documentation** if needed
5. **Ensure tests pass** - run `pytest tests/`
6. **Format your code** - run `ruff format .`
7. **Lint your code** - run `ruff check .`
8. **Write a clear commit message** following [Conventional Commits](https://www.conventionalcommits.org/)
9. **Submit the pull request**

## Development Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- libmagic (for file type detection)

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/folder2md4llms.git
cd folder2md4llms

# Install dependencies with uv
uv sync --all-extras

# Or with pip
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/folder2md4llms --cov-report=html

# Run specific test file
pytest tests/test_cli.py
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy src/folder2md4llms/
```

### Justfile Commands

We provide a `justfile` for common development tasks. If you have [just](https://github.com/casey/just) installed, you can use these commands:

```bash
# Run all tests with coverage
just test

# Format and lint code (auto-fix issues)
just fix

# Check code quality without making changes
just check

# Build distribution packages
just build
```

These commands combine multiple tools and provide a convenient development workflow.

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for function parameters and return values
- Write docstrings for public functions and classes (Google style)
- Keep lines under 88 characters (Ruff/Black default)
- Use meaningful variable and function names

## Git Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to folder2md4llms! 🎉
