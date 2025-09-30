"""Base converter class for document conversion."""

import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Compiled regex patterns for better performance
# Match PDF binary patterns - made more flexible for line-by-line analysis
_BINARY_PATTERN = re.compile(r"%PDF-|xref|<<\/|endobj|endstream|\x00|\xff")
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

    def _sanitize_text(self, text: str, file_path: Path) -> str:
        """Remove binary chunks while preserving readable text.

        Args:
            text: The text to sanitize
            file_path: Path to the source file (for logging)

        Returns:
            Sanitized text with binary content removed
        """
        if not text:
            return text

        # First, split on null bytes and other strong binary markers to preserve text around them
        # Split on null bytes first
        text = text.replace("\x00", "\n[Binary content removed]\n")
        text = text.replace("\xff", "\n[Binary content removed]\n")

        lines = text.split("\n")
        sanitized_lines = []
        removed_chunks = 0
        in_binary_section = False

        for line in lines:
            # Skip already-marked binary content removal markers
            if line == "[Binary content removed]":
                if not in_binary_section:
                    sanitized_lines.append("")
                    sanitized_lines.append(line)
                    sanitized_lines.append("")
                    in_binary_section = True
                    removed_chunks += 1
                continue

            # Check if line contains PDF/document binary patterns
            has_binary = _BINARY_PATTERN.search(line) is not None

            # Check if line has excessive non-printable characters (>30% of line)
            if len(line) > 10:
                non_printable_count = len(_NON_PRINTABLE_PATTERN.findall(line))
                has_excessive_binary = (non_printable_count / len(line)) > 0.3
            else:
                has_excessive_binary = False

            if has_binary or has_excessive_binary:
                if not in_binary_section:
                    # Start of binary section
                    sanitized_lines.append("")
                    sanitized_lines.append("[Binary content removed]")
                    sanitized_lines.append("")
                    in_binary_section = True
                    removed_chunks += 1
            else:
                # Clean line - remove only isolated non-printable characters
                cleaned_line = _NON_PRINTABLE_PATTERN.sub("", line)
                if cleaned_line.strip():  # Only add non-empty lines
                    sanitized_lines.append(cleaned_line)
                    in_binary_section = False

        result = "\n".join(sanitized_lines)

        # Add warning header if content was removed
        if removed_chunks > 0:
            logger.warning(
                f"Removed {removed_chunks} binary chunk(s) from {file_path.name}"
            )
            warning_header = f"[Warning: {removed_chunks} binary section(s) removed from document]\n\n"
            result = warning_header + result

        return result

    def _validate_text_output(
        self, text: str, file_path: Path, validate_binary: bool | None = None
    ) -> str:
        """Validate and sanitize converter output to remove binary content.

        Args:
            text: The text to validate
            file_path: Path to the source file (for logging)
            validate_binary: Override the instance setting for validation

        Returns:
            Sanitized text with binary content removed but readable text preserved
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

        # Check if text contains binary patterns
        has_binary_patterns = _BINARY_PATTERN.search(text) is not None

        # Check for excessive non-printable characters (more than 5% of content)
        has_excessive_binary = False
        if len(text) > 100:
            non_printable_matches = len(_NON_PRINTABLE_PATTERN.findall(text))
            has_excessive_binary = (non_printable_matches / len(text)) > 0.05

        # If binary content detected, sanitize instead of rejecting
        if has_binary_patterns or has_excessive_binary:
            logger.warning(
                f"Binary content detected in {file_path.name}, sanitizing..."
            )
            return self._sanitize_text(text, file_path)

        return text


class ConversionError(Exception):
    """Exception raised during document conversion."""

    pass
