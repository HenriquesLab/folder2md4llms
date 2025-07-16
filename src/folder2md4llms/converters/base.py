"""Base converter class for document conversion."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


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


class ConversionError(Exception):
    """Exception raised during document conversion."""

    pass
