"""Python code converter for extracting signatures and condensing code."""

from pathlib import Path

from ..analyzers.code_analyzer import PythonCodeAnalyzer
from .base import BaseConverter


class PythonConverter(BaseConverter):
    """Converter for Python files to extract signatures and docstrings."""

    def __init__(self, config: dict | None = None):
        """Initialize the Python converter.

        Args:
            config: Configuration dictionary with optional keys:
                - condense_python: Whether to condense Python code
                - python_condense_mode: Mode for condensing ("signatures", "signatures_with_docstrings", "structure")
        """
        super().__init__(config)
        self.condense_python = config.get("condense_python", False) if config else False
        self.condense_mode = (
            config.get("python_condense_mode", "signatures_with_docstrings")
            if config
            else "signatures_with_docstrings"
        )

        if self.condense_python:
            self.analyzer: PythonCodeAnalyzer | None = PythonCodeAnalyzer(
                condense_mode=self.condense_mode
            )
        else:
            self.analyzer = None

    def can_convert(self, file_path: Path) -> bool:
        """Check if this converter can handle the file.

        Args:
            file_path: Path to the file

        Returns:
            True if this converter can handle Python files and condensing is enabled
        """
        return self.condense_python and file_path.suffix.lower() == ".py"

    def convert(self, file_path: Path) -> str | None:
        """Convert Python file to condensed format.

        Args:
            file_path: Path to the Python file

        Returns:
            Condensed Python code or None if conversion failed
        """
        if not self.analyzer:
            return None

        try:
            result = self.analyzer.analyze_file(file_path)

            if result:
                # Add metadata header
                header = f"# Python Code Analysis: {file_path.name}\n"
                header += f"# Condensed using mode: {self.condense_mode}\n"
                header += f"# Original file: {file_path}\n\n"

                return header + result

            return None

        except Exception as e:
            return f"# Error processing Python file {file_path}: {e}"

    def get_supported_extensions(self) -> set:
        """Get supported file extensions.

        Returns:
            Set of supported file extensions
        """
        return {".py"}

    def get_file_extensions(self) -> list[str]:
        """Get supported file extensions.

        Returns:
            List of supported file extensions
        """
        return [".py"]

    def get_conversion_info(self) -> dict:
        """Get information about this converter.

        Returns:
            Dictionary with converter information
        """
        return {
            "name": "Python Code Analyzer",
            "description": "Extracts signatures, docstrings, and structure from Python files",
            "supported_extensions": self.get_file_extensions(),
            "condense_python": self.condense_python,
            "condense_mode": self.condense_mode,
            "dependencies": ["ast (built-in)"],
        }
