"""Base converter class for document conversion."""

import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Compiled regex patterns for better performance
_BINARY_PATTERN = re.compile(r"%PDF-|xref[\n ]|<<\/|endobj|endstream|\x00|\xff")
_NON_PRINTABLE_PATTERN = re.compile(r"[^\x20-\x7E\s]")


class BaseConverter(ABC):
    """Base class for document converters."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        # Performance optimization: allow disabling binary validation for trusted sources
        self.validate_binary_output = self.config.get("validate_binary_output", True)

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

    def _validate_text_output(
        self, text: str, file_path: Path, validate_binary: bool | None = None
    ) -> str:
        """Validate that converter output doesn't contain binary content.

        Args:
            text: The text to validate
            file_path: Path to the source file (for logging)
            validate_binary: Override the instance setting for validation
        """
        if not text:
            return text

        # Allow per-call override of validation setting
        should_validate = (
            validate_binary
            if validate_binary is not None
            else self.validate_binary_output
        )
        if not should_validate:
            return text

        # Use compiled regex for better performance
        if _BINARY_PATTERN.search(text):
            logger.error(f"Binary content detected in converter output for {file_path}")
            return "[Error: Binary content detected in document conversion - file may be corrupted or unsupported]"

        # Check for excessive non-printable characters (more than 5% of content)
        # Use compiled regex for better performance
        if len(text) > 100:
            non_printable_matches = len(_NON_PRINTABLE_PATTERN.findall(text))
            if non_printable_matches / len(text) > 0.05:
                logger.warning(
                    f"High percentage of non-printable characters in {file_path}"
                )
                return f"[Warning: Document contains significant non-text content - conversion may be incomplete]\n\n{text[:1000]}..."

        return text


class ConversionError(Exception):
    """Exception raised during document conversion."""

    pass
