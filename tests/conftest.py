"""Pytest configuration and fixtures."""

import shutil
import tempfile
from pathlib import Path

import pytest

from folder2md4llms.utils.config import Config
from folder2md4llms.utils.ignore_patterns import IgnorePatterns


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_repo(temp_dir):
    """Create a sample repository structure for testing."""
    repo_path = temp_dir / "sample_repo"
    repo_path.mkdir()

    # Create some test files
    (repo_path / "README.md").write_text("# Test Repository")
    (repo_path / "main.py").write_text("print('Hello, World!')")
    (repo_path / "config.json").write_text('{"key": "value"}')

    # Create subdirectories
    src_dir = repo_path / "src"
    src_dir.mkdir()
    (src_dir / "module.py").write_text("def test_function():\n    pass")

    tests_dir = repo_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_module.py").write_text("def test_example():\n    assert True")

    # Create a binary file
    (repo_path / "binary.dat").write_bytes(b"\x00\x01\x02\x03")

    return repo_path


@pytest.fixture
def config():
    """Create a default config for testing."""
    return Config()


@pytest.fixture
def ignore_patterns():
    """Create default ignore patterns for testing."""
    return IgnorePatterns()


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"


@pytest.fixture
def sample_docx_content():
    """Sample DOCX content for testing."""
    return b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!"


@pytest.fixture
def sample_xlsx_content():
    """Sample XLSX content for testing."""
    return b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!"
