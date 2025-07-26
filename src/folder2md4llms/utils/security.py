"""Security utilities for folder2md4llms."""

import os
from pathlib import Path


def safe_path_join(base: Path, *parts: str) -> Path:
    """Safely join paths preventing directory traversal.

    Args:
        base: The base path that should contain all joined paths
        *parts: Path parts to join

    Returns:
        The safely joined path

    Raises:
        ValueError: If the resulting path would escape the base directory
    """
    # Resolve the base path
    base = base.resolve()

    # Join and resolve the full path
    full_path = base.joinpath(*parts).resolve()

    # Ensure the full path is under the base path
    try:
        full_path.relative_to(base)
    except ValueError as e:
        raise ValueError(f"Path traversal attempt detected: {full_path}") from e

    return full_path


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations.

    Args:
        filename: The filename to sanitize

    Returns:
        A sanitized filename safe for file operations
    """
    # Remove path separators and null bytes
    invalid_chars = ["/", "\\", "\0", ".."]
    for char in invalid_chars:
        filename = filename.replace(char, "_")

    # Remove other potentially dangerous characters
    filename = "".join(c for c in filename if c.isprintable() and c not in '<>:"|?*')

    # Limit length
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[: max_length - len(ext)] + ext

    # Ensure filename is not empty
    if not filename:
        filename = "unnamed"

    return filename


def validate_path_within_repo(path: Path, repo_path: Path) -> bool:
    """Validate that a path is within the repository boundaries.

    Args:
        path: The path to validate
        repo_path: The repository root path

    Returns:
        True if the path is valid and within repo, False otherwise
    """
    try:
        # Resolve both paths
        path = path.resolve()
        repo_path = repo_path.resolve()

        # Check if path is relative to repo_path
        path.relative_to(repo_path)
        return True
    except (ValueError, RuntimeError):
        return False


def secure_file_read(
    file_path: Path, repo_path: Path, encoding: str = "utf-8"
) -> str | None:
    """Securely read a file ensuring it's within the repository.

    Args:
        file_path: The file to read
        repo_path: The repository root path
        encoding: File encoding (default: utf-8)

    Returns:
        File contents if successful, None if security check fails
    """
    if not validate_path_within_repo(file_path, repo_path):
        return None

    try:
        with open(file_path, encoding=encoding) as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None
