"""Base converter class for document conversion."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BaseConverter(ABC):
    """Base class for document converters."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    @abstractmethod
    def can_convert(self, file_path: Path) -> bool:
        """Check if this converter can handle the given file."""
        pass

    @abstractmethod
    def convert(self, file_path: Path) -> str | None:
        """Convert the file to text/markdown format."""
        pass

    @abstractmethod
    def get_supported_extensions(self) -> set:
        """Get the file extensions this converter supports."""
        pass

    def get_file_info(self, file_path: Path) -> dict[str, Any]:
        """Get basic information about the file."""
        try:
            stat = file_path.stat()
            return {
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "extension": file_path.suffix.lower(),
                "name": file_path.name,
            }
        except OSError:
            return {
                "size": 0,
                "modified": 0,
                "extension": "",
                "name": str(file_path),
            }

    def _validate_text_output(self, text: str, file_path: Path) -> str:
        """Validate that converter output doesn't contain binary content."""
        if not text:
            return text

        # Check for common binary content patterns that should never appear in text
        binary_indicators = [
            "%PDF-",  # PDF headers
            "xref\n",  # PDF xref tables
            "xref ",  # PDF xref tables (space variant)
            "<</",  # PDF objects
            "endobj",  # PDF object ends
            "endstream",  # PDF streams
            "\x00",  # Null bytes
            "\xff",  # Binary markers
        ]

        for indicator in binary_indicators:
            if indicator in text:
                logger.error(
                    f"Binary content detected in converter output for {file_path}"
                )
                return "[Error: Binary content detected in document conversion - file may be corrupted or unsupported]"

        # Check for excessive non-printable characters (more than 5% of content)
        printable_chars = sum(1 for c in text if c.isprintable() or c.isspace())
        if len(text) > 100 and printable_chars / len(text) < 0.95:
            logger.warning(
                f"High percentage of non-printable characters in {file_path}"
            )
            return f"[Warning: Document contains significant non-text content - conversion may be incomplete]\n\n{text[:1000]}..."

        return text


class ConversionError(Exception):
    """Exception raised during document conversion."""

    pass
