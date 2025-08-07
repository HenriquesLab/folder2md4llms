"""Tests for security utilities."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from folder2md4llms.utils.security import (
    safe_path_join,
    sanitize_filename,
    secure_file_read,
    validate_path_within_repo,
)


class TestSafePathJoin:
    """Test safe_path_join function."""

    def test_normal_path_join(self, tmp_path):
        """Test normal path joining works."""
        base = tmp_path
        result = safe_path_join(base, "subdir", "file.txt")
        expected = base / "subdir" / "file.txt"
        assert result == expected.resolve()

    def test_path_traversal_prevention(self, tmp_path):
        """Test that path traversal attempts are blocked."""
        base = tmp_path

        # Test various path traversal attempts
        traversal_attempts = [
            ["../", "etc", "passwd"],
            ["..", "etc", "passwd"],
            ["subdir", "..", "..", "etc", "passwd"],
            ["..\\", "windows", "system32"],  # Windows style (only on Windows)
            # ["..", "\\", "etc", "passwd"],  # Mixed separators (Unix treats \\ as literal)
        ]

        for attempt in traversal_attempts:
            # Skip Windows-specific tests on Unix
            if any("\\" in part for part in attempt) and os.name != "nt":
                continue
            with pytest.raises(ValueError, match="Path traversal attempt detected"):
                safe_path_join(base, *attempt)

    def test_relative_paths_within_base(self, tmp_path):
        """Test that relative paths within base directory work."""
        base = tmp_path
        subdir = base / "subdir"
        subdir.mkdir()

        # These should work as they stay within base
        result = safe_path_join(base, "subdir")
        assert result == subdir.resolve()

        result = safe_path_join(base, "subdir", "file.txt")
        assert result == (subdir / "file.txt").resolve()

    def test_absolute_paths_within_base(self, tmp_path):
        """Test absolute paths that resolve within base directory."""
        base = tmp_path
        subdir = base / "subdir"
        subdir.mkdir()

        # This should work as it resolves within base
        result = safe_path_join(base, str(subdir.name))
        assert result == subdir.resolve()

    def test_symlink_traversal_prevention(self, tmp_path):
        """Test that symlink-based traversal is prevented."""
        base = tmp_path
        outside = tmp_path.parent / "outside"
        outside.mkdir()

        # Create a symlink that points outside base
        symlink_path = base / "bad_link"
        try:
            symlink_path.symlink_to(outside)

            # This should be blocked
            with pytest.raises(ValueError, match="Path traversal attempt detected"):
                safe_path_join(base, "bad_link")

        except OSError:
            # Skip if symlinks not supported (e.g., Windows without permissions)
            pytest.skip("Symlinks not supported on this system")

    def test_empty_parts(self, tmp_path):
        """Test handling of empty path parts."""
        base = tmp_path
        result = safe_path_join(base, "", "file.txt", "")
        expected = base / "file.txt"
        assert result == expected.resolve()


class TestSanitizeFilename:
    """Test sanitize_filename function."""

    def test_basic_filename(self):
        """Test normal filename passes through unchanged."""
        filename = "normal_file.txt"
        result = sanitize_filename(filename)
        assert result == filename

    def test_path_separator_removal(self):
        """Test that path separators are replaced with underscores."""
        dangerous_names = [
            "path/to/file.txt",
            "path\\to\\file.txt",
            "file\x00.txt",  # null byte
            "file..txt",  # double dot
        ]

        for dangerous in dangerous_names:
            result = sanitize_filename(dangerous)
            assert "/" not in result
            assert "\\" not in result
            assert "\x00" not in result
            assert ".." not in result
            assert "_" in result  # Should be replaced with underscore

    def test_dangerous_characters_removal(self):
        """Test removal of dangerous filename characters."""
        dangerous_chars = '<>:"|?*'
        filename = f"file{dangerous_chars}name.txt"
        result = sanitize_filename(filename)

        for char in dangerous_chars:
            assert char not in result

        # Should still have the base filename parts
        assert "file" in result
        assert "name" in result
        assert ".txt" in result

    def test_non_printable_removal(self):
        """Test removal of non-printable characters."""
        filename = "file\x01\x02\x03name.txt"
        result = sanitize_filename(filename)

        # Non-printable chars should be removed
        assert "\x01" not in result
        assert "\x02" not in result
        assert "\x03" not in result

        # Printable parts should remain
        assert "filename" in result
        assert ".txt" in result

    def test_length_limiting(self):
        """Test that very long filenames are truncated."""
        # Create a filename longer than 255 characters
        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name)

        assert len(result) <= 255
        assert result.endswith(".txt")  # Extension should be preserved

    def test_empty_filename_fallback(self):
        """Test fallback for empty or invalid filenames."""
        empty_names = [
            "",
            "\x00\x01\x02",  # Only non-printable
            "/\\",  # Only path separators
            '<>:|"?*',  # Only dangerous chars
        ]

        expected_results = {
            "": "unnamed",
            "\x00\x01\x02": "_",  # Non-printable chars become underscores
            "/\\": "__",  # Path separators become underscores
            '<>:|"?*': "unnamed",  # Only dangerous chars, results in empty, fallback to unnamed
        }

        for empty_name in empty_names:
            result = sanitize_filename(empty_name)
            expected = expected_results[empty_name]
            assert result == expected, (
                f"Expected {expected} for {repr(empty_name)}, got {repr(result)}"
            )

    def test_unicode_handling(self):
        """Test proper handling of Unicode characters."""
        unicode_filename = "résumé_文档.pdf"
        result = sanitize_filename(unicode_filename)

        # Unicode should be preserved if printable
        assert "résumé" in result
        assert "文档" in result
        assert ".pdf" in result


class TestValidatePathWithinRepo:
    """Test validate_path_within_repo function."""

    def test_valid_path_within_repo(self, tmp_path):
        """Test that valid paths within repo return True."""
        repo = tmp_path / "repo"
        repo.mkdir()

        subdir = repo / "subdir"
        subdir.mkdir()

        file_path = subdir / "file.txt"
        file_path.touch()

        assert validate_path_within_repo(file_path, repo) is True
        assert validate_path_within_repo(subdir, repo) is True

    def test_path_outside_repo(self, tmp_path):
        """Test that paths outside repo return False."""
        repo = tmp_path / "repo"
        repo.mkdir()

        outside = tmp_path / "outside"
        outside.mkdir()

        outside_file = outside / "file.txt"
        outside_file.touch()

        assert validate_path_within_repo(outside_file, repo) is False
        assert validate_path_within_repo(outside, repo) is False

    def test_path_traversal_attempts(self, tmp_path):
        """Test that path traversal attempts return False."""
        repo = tmp_path / "repo"
        repo.mkdir()

        # Create a file outside repo
        outside = tmp_path / "outside.txt"
        outside.touch()

        # Try to access it via path traversal
        traversal_path = repo / ".." / "outside.txt"
        assert validate_path_within_repo(traversal_path, repo) is False

    def test_symlink_outside_repo(self, tmp_path):
        """Test that symlinks pointing outside repo return False."""
        repo = tmp_path / "repo"
        repo.mkdir()

        outside = tmp_path / "outside.txt"
        outside.touch()

        try:
            # Create symlink inside repo pointing outside
            symlink = repo / "bad_link.txt"
            symlink.symlink_to(outside)

            assert validate_path_within_repo(symlink, repo) is False

        except OSError:
            # Skip if symlinks not supported
            pytest.skip("Symlinks not supported on this system")

    def test_non_existent_paths(self, tmp_path):
        """Test handling of non-existent paths."""
        repo = tmp_path / "repo"
        repo.mkdir()

        non_existent = repo / "does_not_exist.txt"
        # This should still return True as it would be within repo if it existed
        assert validate_path_within_repo(non_existent, repo) is True

        # Outside repo should still return False
        outside_non_existent = tmp_path / "outside_does_not_exist.txt"
        assert validate_path_within_repo(outside_non_existent, repo) is False

    def test_runtime_error_handling(self, tmp_path):
        """Test handling of RuntimeError exceptions."""
        repo = tmp_path / "repo"
        repo.mkdir()

        # Mock Path.relative_to to raise RuntimeError
        with patch.object(Path, "relative_to", side_effect=RuntimeError("Test error")):
            result = validate_path_within_repo(repo / "file.txt", repo)
            assert result is False


class TestSecureFileRead:
    """Test secure_file_read function."""

    def test_read_valid_file(self, tmp_path):
        """Test reading a valid file within repo."""
        repo = tmp_path / "repo"
        repo.mkdir()

        file_path = repo / "test.txt"
        test_content = "Hello, World!"
        file_path.write_text(test_content, encoding="utf-8")

        result = secure_file_read(file_path, repo)
        assert result == test_content

    def test_read_file_outside_repo(self, tmp_path):
        """Test that reading files outside repo returns None."""
        repo = tmp_path / "repo"
        repo.mkdir()

        outside = tmp_path / "outside.txt"
        outside.write_text("Secret content")

        result = secure_file_read(outside, repo)
        assert result is None

    def test_read_non_existent_file(self, tmp_path):
        """Test reading non-existent file returns None."""
        repo = tmp_path / "repo"
        repo.mkdir()

        non_existent = repo / "does_not_exist.txt"
        result = secure_file_read(non_existent, repo)
        assert result is None

    def test_read_file_with_encoding_issues(self, tmp_path):
        """Test handling of encoding issues."""
        repo = tmp_path / "repo"
        repo.mkdir()

        file_path = repo / "binary.txt"
        # Write binary data that's not valid UTF-8
        file_path.write_bytes(b"\xff\xfe\x00\x00")

        result = secure_file_read(file_path, repo)
        assert result is None

    def test_custom_encoding(self, tmp_path):
        """Test reading with custom encoding."""
        repo = tmp_path / "repo"
        repo.mkdir()

        file_path = repo / "latin1.txt"
        content = "Café"
        file_path.write_text(content, encoding="latin1")

        # Should work with correct encoding
        result = secure_file_read(file_path, repo, encoding="latin1")
        assert result == content

        # Should fail with wrong encoding
        result = secure_file_read(file_path, repo, encoding="utf-8")
        assert result is None

    def test_permission_denied(self, tmp_path):
        """Test handling of permission denied errors."""
        repo = tmp_path / "repo"
        repo.mkdir()

        file_path = repo / "restricted.txt"
        file_path.write_text("Secret")

        # Mock open to raise PermissionError
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            result = secure_file_read(file_path, repo)
            assert result is None

    def test_path_traversal_in_secure_read(self, tmp_path):
        """Test that path traversal is blocked in secure read."""
        repo = tmp_path / "repo"
        repo.mkdir()

        # Create file outside repo
        outside = tmp_path / "secret.txt"
        outside.write_text("Secret content")

        # Try to read via path traversal
        traversal_path = repo / ".." / "secret.txt"
        result = secure_file_read(traversal_path, repo)
        assert result is None
