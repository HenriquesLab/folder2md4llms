"""Tests for the main repository processor."""

from pathlib import Path

import pytest

from folder2md4llms.processor import RepositoryProcessor


class TestRepositoryProcessor:
    """Test the RepositoryProcessor class."""

    def test_process_basic_repository(self, sample_repo, config):
        """Test processing a basic repository."""
        processor = RepositoryProcessor(config)

        result = processor.process(sample_repo)

        assert isinstance(result, str)
        assert "# Repository: sample_repo" in result
        assert "## 📁 Folder Structure" in result
        assert "## 📊 Repository Statistics" in result
        assert "## 📄 Source Code" in result

    def test_process_with_no_tree(self, sample_repo, config):
        """Test processing without tree structure."""
        config.include_tree = False
        processor = RepositoryProcessor(config)

        result = processor.process(sample_repo)

        assert "📁 Folder Structure" not in result
        assert "📊 Repository Statistics" in result
        assert "📄 Source Code" in result

    def test_process_with_no_stats(self, sample_repo, config):
        """Test processing without statistics."""
        config.include_stats = False
        processor = RepositoryProcessor(config)

        result = processor.process(sample_repo)

        assert "📁 Folder Structure" in result
        assert "📊 Repository Statistics" not in result
        assert "📄 Source Code" in result

    def test_process_with_no_doc_conversion(self, sample_repo, config):
        """Test processing without document conversion."""
        config.convert_docs = False
        processor = RepositoryProcessor(config)

        result = processor.process(sample_repo)

        assert "📄 Source Code" in result
        # Should not have document conversion section
        assert "📋 Documents" not in result

    def test_process_with_no_binary_description(self, sample_repo, config):
        """Test processing without binary file description."""
        config.describe_binaries = False
        processor = RepositoryProcessor(config)

        result = processor.process(sample_repo)

        assert "📄 Source Code" in result
        # Should not have binary files section
        assert "🔧 Binary Files" not in result

    def test_process_with_small_file_size_limit(self, sample_repo, config):
        """Test processing with small file size limit."""
        config.max_file_size = 10  # Very small limit
        processor = RepositoryProcessor(config)

        result = processor.process(sample_repo)

        # Should still process and create output (may skip large files)
        assert "# Repository: sample_repo" in result
        # May or may not have source code section due to size limits
        assert "📊 Repository Statistics" in result

    def test_process_nonexistent_directory(self, config):
        """Test processing nonexistent directory."""
        processor = RepositoryProcessor(config)

        with pytest.raises(ValueError, match="Invalid repository path"):
            processor.process(Path("/nonexistent/directory"))

    def test_process_file_instead_of_directory(self, temp_dir, config):
        """Test processing file instead of directory."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        processor = RepositoryProcessor(config)

        with pytest.raises(ValueError, match="Invalid repository path"):
            processor.process(test_file)

    def test_process_empty_directory(self, temp_dir, config):
        """Test processing empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        processor = RepositoryProcessor(config)

        result = processor.process(empty_dir)

        assert "# Repository: empty" in result
        assert "Total Files:** 0" in result

    def test_process_with_ignore_patterns(self, sample_repo, config, temp_dir):
        """Test processing with custom ignore patterns."""
        # Create custom ignore file
        ignore_file = temp_dir / ".folder2md_ignore"
        ignore_file.write_text("*.py\n")

        config.ignore_file = ignore_file
        processor = RepositoryProcessor(config)

        result = processor.process(sample_repo)

        # Should not contain Python files
        assert "main.py" not in result
        assert "module.py" not in result
        # But should contain other files
        assert "README.md" in result

    def test_process_statistics_calculation(self, sample_repo, config):
        """Test that statistics are calculated correctly."""
        processor = RepositoryProcessor(config)

        result = processor.process(sample_repo)

        # Check that statistics section contains expected info
        assert "Total Files:**" in result
        assert "Text Files:**" in result
        assert "Binary Files:**" in result
        assert "Languages" in result

    def test_process_markdown_formatting(self, sample_repo, config):
        """Test that output is properly formatted as markdown."""
        processor = RepositoryProcessor(config)

        result = processor.process(sample_repo)

        # Check markdown formatting
        assert result.startswith("# Repository:")
        assert "## 📑 Table of Contents" in result
        assert "```" in result  # Code blocks
        assert "**" in result  # Bold text
        assert "- " in result  # List items

    def test_process_with_various_file_types(self, temp_dir, config):
        """Test processing directory with various file types."""
        # Create directory with different file types
        test_dir = temp_dir / "test_repo"
        test_dir.mkdir()

        # Text files
        (test_dir / "script.py").write_text("print('hello')")
        (test_dir / "data.json").write_text('{"key": "value"}')
        (test_dir / "readme.md").write_text("# README")

        # Binary files
        (test_dir / "binary.dat").write_bytes(b"\x00\x01\x02\x03")
        (test_dir / "image.jpg").write_bytes(b"\xff\xd8\xff")

        processor = RepositoryProcessor(config)

        result = processor.process(test_dir)

        # Should process text files
        assert "script.py" in result
        assert "print('hello')" in result

        # Should describe binary files
        assert "binary.dat" in result or "image.jpg" in result
