"""RTF document converter."""

import logging
from pathlib import Path
from typing import Any

try:
    from striprtf.striprtf import rtf_to_text

    RTF_AVAILABLE = True
except ImportError:
    RTF_AVAILABLE = False

from .base import BaseConverter, ConversionError

logger = logging.getLogger(__name__)


class RTFConverter(BaseConverter):
    """Converts RTF files to text."""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.max_size = self.config.get("rtf_max_size", 10 * 1024 * 1024)  # 10MB

    def can_convert(self, file_path: Path) -> bool:
        """Check if this converter can handle the given file."""
        return (
            RTF_AVAILABLE and file_path.suffix.lower() == ".rtf" and file_path.exists()
        )

    def convert(self, file_path: Path) -> str | None:
        """Convert RTF to text."""
        if not RTF_AVAILABLE:
            return (
                "RTF conversion not available. Install striprtf: pip install striprtf"
            )

        try:
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.max_size:
                return f"RTF file too large ({file_size} bytes, max {self.max_size})"

            # Read RTF file
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                rtf_content = f.read()

            # Convert RTF to plain text
            text_content = rtf_to_text(rtf_content)

            if not text_content.strip():
                return "RTF file appears to be empty or contains no readable text"

            # Format the output
            text_parts = []
            text_parts.append(f"RTF Document: {file_path.name}")
            text_parts.append(f"File size: {file_size} bytes")
            text_parts.append("=" * 50)
            text_parts.append("")
            text_parts.append(text_content.strip())

            return "\n".join(text_parts)

        except Exception as e:
            logger.error(f"Error converting RTF {file_path}: {e}")
            raise ConversionError(f"Failed to convert RTF: {str(e)}") from e

    def get_supported_extensions(self) -> set:
        """Get the file extensions this converter supports."""
        return {".rtf"}

    def get_document_info(self, file_path: Path) -> dict[str, Any]:
        """Get RTF-specific information."""
        info = self.get_file_info(file_path)

        if not RTF_AVAILABLE:
            info["error"] = "RTF library not available"
            return info

        try:
            file_size = file_path.stat().st_size
            info.update(
                {
                    "file_size": file_size,
                    "can_convert": file_size <= self.max_size,
                }
            )

            if file_size > self.max_size:
                info["warning"] = (
                    f"File too large for conversion (max {self.max_size} bytes)"
                )

        except Exception as e:
            info["error"] = str(e)

        return info
