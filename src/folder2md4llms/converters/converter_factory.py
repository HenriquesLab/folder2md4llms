"""Factory for creating document converters."""

from pathlib import Path
from typing import Any

from .base import BaseConverter
from .code_converter import CodeConverter
from .docx_converter import DOCXConverter
from .notebook_converter import NotebookConverter
from .pdf_converter import PDFConverter
from .pptx_converter import PPTXConverter
from .python_converter import PythonConverter
from .rtf_converter import RTFConverter
from .xlsx_converter import XLSXConverter


class ConverterFactory:
    """Factory for creating appropriate document converters."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self._converters: list[BaseConverter] | None = None

    def _get_converters(self) -> list[BaseConverter]:
        """Get all available converters."""
        if self._converters is None:
            self._converters = [
                CodeConverter(
                    self.config
                ),  # Check multi-language code condensing first
                PythonConverter(self.config),  # Check Python condensing
                PDFConverter(self.config),
                DOCXConverter(self.config),
                XLSXConverter(self.config),
                RTFConverter(self.config),
                NotebookConverter(self.config),
                PPTXConverter(self.config),
            ]
        return self._converters

    def get_converter(self, file_path: Path) -> BaseConverter | None:
        """Get the appropriate converter for a file."""
        for converter in self._get_converters():
            if converter.can_convert(file_path):
                return converter
        return None

    def can_convert(self, file_path: Path) -> bool:
        """Check if any converter can handle the file."""
        return self.get_converter(file_path) is not None

    def convert_file(self, file_path: Path) -> str | None:
        """Convert a file using the appropriate converter."""
        converter = self.get_converter(file_path)
        if converter:
            return converter.convert(file_path)
        return None

    def get_supported_extensions(self) -> set:
        """Get all supported file extensions."""
        extensions = set()
        for converter in self._get_converters():
            extensions.update(converter.get_supported_extensions())
        return extensions

    def get_file_info(self, file_path: Path) -> dict[str, Any]:
        """Get file information using the appropriate converter."""
        converter = self.get_converter(file_path)
        if converter and hasattr(converter, "get_document_info"):
            info = converter.get_document_info(file_path)
            return info if isinstance(info, dict) else {}
        else:
            # Return basic file info
            try:
                stat = file_path.stat()
                return {
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "extension": file_path.suffix.lower(),
                    "name": file_path.name,
                    "supported": False,
                }
            except OSError:
                return {
                    "size": 0,
                    "modified": 0,
                    "extension": "",
                    "name": str(file_path),
                    "supported": False,
                }
