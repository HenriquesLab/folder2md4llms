"""Centralized encoding and file reading utilities.

This module provides consistent file reading with encoding fallback
and Unicode surrogate character handling across the entire codebase.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def clean_surrogates(text: str) -> str:
    """Remove surrogate characters from text.

    Surrogate characters can appear when reading files with improper encoding,
    particularly when using latin-1 fallback. They cause errors when writing
    to files or copying to clipboard.

    Args:
        text: Text that may contain surrogate characters

    Returns:
        Text with all surrogates replaced with the Unicode replacement character
    """
    if not text:
        return text

    try:
        # Test if text can be encoded to UTF-8
        text.encode("utf-8")
        return text
    except UnicodeEncodeError:
        # Contains surrogates, clean them
        return text.encode("utf-8", errors="replace").decode("utf-8")


def read_file_with_encoding(
    file_path: Path,
    fallback_encodings: list[str] | None = None,
    max_size: int | None = None,
) -> str:
    """Read a file with automatic encoding detection and fallback.

    This function tries multiple encodings in order and automatically
    cleans any surrogate characters that may have been introduced.

    Args:
        file_path: Path to the file to read
        fallback_encodings: List of encodings to try. Defaults to
            ["utf-8", "utf-16", "latin-1", "ascii"]
        max_size: Maximum file size in bytes. If specified, returns None
            for files exceeding this size.

    Returns:
        File contents as a string with surrogates removed

    Raises:
        OSError: If file cannot be read
        PermissionError: If lacking permissions to read file
    """
    if fallback_encodings is None:
        fallback_encodings = ["utf-8", "utf-16", "latin-1", "ascii"]

    # Check file size if limit specified
    if max_size is not None:
        file_size = file_path.stat().st_size
        if file_size > max_size:
            raise ValueError(
                f"File size ({file_size} bytes) exceeds maximum ({max_size} bytes)"
            )

    # Try each encoding in order
    last_error = None
    for encoding in fallback_encodings:
        try:
            with open(file_path, encoding=encoding, errors="replace") as f:
                content = f.read()

            # Clean any surrogate characters that might have slipped through
            content = clean_surrogates(content)

            logger.debug(f"Successfully read {file_path} with {encoding} encoding")
            return content

        except UnicodeDecodeError as e:
            last_error = e
            logger.debug(f"Failed to read {file_path} with {encoding}: {e}")
            continue
        except (OSError, PermissionError):
            # Don't try other encodings for I/O errors
            raise

    # If all encodings failed, raise the last error
    if last_error:
        raise UnicodeDecodeError(
            "utf-8",
            b"",
            0,
            1,
            f"Could not decode {file_path} with any encoding: {fallback_encodings}",
        ) from last_error

    # Should never reach here, but just in case
    raise OSError(f"Failed to read {file_path}")


def read_file_safely(
    file_path: Path,
    max_size: int | None = None,
) -> str | None:
    """Read a file safely, returning None on any error.

    This is a wrapper around read_file_with_encoding() that catches
    all exceptions and returns None instead of raising.

    Args:
        file_path: Path to the file to read
        max_size: Maximum file size in bytes

    Returns:
        File contents as string, or None if reading failed
    """
    try:
        return read_file_with_encoding(file_path, max_size=max_size)
    except (OSError, PermissionError, UnicodeDecodeError, ValueError):
        logger.debug(f"Failed to read {file_path} safely")
        return None
    except Exception as e:
        # Catch any platform-specific errors
        logger.warning(f"Unexpected error reading {file_path}: {e}")
        return None
