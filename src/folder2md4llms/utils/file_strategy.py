"""Centralized file processing strategy determination."""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .file_utils import (
    get_language_from_extension,
    is_archive_file,
    is_binary_file,
    is_data_file,
    is_executable_file,
    is_image_file,
    should_condense_code_file,
    should_condense_python_file,
    should_convert_file,
)

logger = logging.getLogger(__name__)


class ProcessingAction(Enum):
    """Actions that can be taken on a file."""

    SKIP = "skip"
    CONVERT = "convert"
    READ_TEXT = "read_text"
    CONDENSE_PYTHON = "condense_python"
    CONDENSE_CODE = "condense_code"
    ANALYZE_BINARY = "analyze_binary"


@dataclass
class FileProcessingStrategy:
    """Complete strategy for processing a file."""

    action: ProcessingAction
    priority: int = 0  # Higher = more important
    reason: str = ""
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class FileStrategyDeterminer:
    """Determines the appropriate processing strategy for files."""

    def __init__(self, config: dict[str, Any]):
        self.config = config

    def get_strategy(self, file_path: Path) -> FileProcessingStrategy:
        """Determine the complete processing strategy for a file."""
        try:
            # Get basic file information
            is_binary = is_binary_file(file_path)
            extension = file_path.suffix.lower()
            language = get_language_from_extension(extension)

            # Create metadata
            metadata = {
                "extension": extension,
                "language": language,
                "is_binary": is_binary,
                "size": file_path.stat().st_size if file_path.exists() else 0,
            }

            # Determine processing action based on file type and configuration
            strategy = self._determine_action(file_path, is_binary, metadata)
            if strategy.metadata is None:
                strategy.metadata = {}
            strategy.metadata.update(metadata)

            return strategy

        except Exception as e:
            logger.warning(f"Error determining strategy for {file_path}: {e}")
            return FileProcessingStrategy(
                action=ProcessingAction.SKIP,
                reason=f"Error analyzing file: {e}",
                metadata={"error": str(e)},
            )

    def _determine_action(
        self, file_path: Path, is_binary: bool, metadata: dict
    ) -> FileProcessingStrategy:
        """Determine the specific action to take on a file."""

        # 1. Check if file should be converted (documents)
        if should_convert_file(file_path):
            return FileProcessingStrategy(
                action=ProcessingAction.CONVERT,
                priority=self._get_convert_priority(file_path),
                reason="Document file that can be converted to text",
            )

        # 2. Check for Python condensing (highest priority for code)
        if should_condense_python_file(
            file_path, self.config.get("condense_python", False)
        ):
            return FileProcessingStrategy(
                action=ProcessingAction.CONDENSE_PYTHON,
                priority=100,  # High priority for Python files
                reason="Python file eligible for smart condensing",
            )

        # 3. Check for general code condensing
        if should_condense_code_file(
            file_path,
            self.config.get("condense_code", False),
            self.config.get("condense_languages", []),
        ):
            return FileProcessingStrategy(
                action=ProcessingAction.CONDENSE_CODE,
                priority=90,  # High priority for code files
                reason="Code file eligible for smart condensing",
            )

        # 4. Handle binary files
        if is_binary:
            # Check if it's a data file that might be interesting
            if is_data_file(file_path):
                return FileProcessingStrategy(
                    action=ProcessingAction.ANALYZE_BINARY,
                    priority=10,
                    reason="Binary data file - analyze metadata only",
                )

            # Check if it's an image, archive, or executable
            if is_image_file(file_path):
                return FileProcessingStrategy(
                    action=ProcessingAction.SKIP,
                    priority=0,
                    reason="Image file - skipping content",
                )

            if is_archive_file(file_path):
                return FileProcessingStrategy(
                    action=ProcessingAction.SKIP,
                    priority=0,
                    reason="Archive file - skipping content",
                )

            if is_executable_file(file_path):
                return FileProcessingStrategy(
                    action=ProcessingAction.SKIP,
                    priority=0,
                    reason="Executable file - skipping content",
                )

            # Unknown binary file - analyze if small enough
            file_size = metadata.get("size", 0)
            if file_size < 1024 * 1024:  # 1MB limit for binary analysis
                return FileProcessingStrategy(
                    action=ProcessingAction.ANALYZE_BINARY,
                    priority=5,
                    reason="Small binary file - analyze metadata",
                )
            else:
                return FileProcessingStrategy(
                    action=ProcessingAction.SKIP,
                    priority=0,
                    reason="Large binary file - skipping",
                )

        # 5. Handle text files
        else:
            # Determine priority based on file type and size
            priority = self._get_text_file_priority(file_path, metadata)

            return FileProcessingStrategy(
                action=ProcessingAction.READ_TEXT,
                priority=priority,
                reason="Text file - read content",
            )

    def _get_convert_priority(self, file_path: Path) -> int:
        """Get priority for convertible files."""
        extension = file_path.suffix.lower()

        # Higher priority for common document types
        high_priority_docs = {".pdf", ".docx", ".xlsx", ".pptx"}
        if extension in high_priority_docs:
            return 80

        # Medium priority for other documents
        return 60

    def _get_text_file_priority(self, file_path: Path, metadata: dict) -> int:
        """Get priority for text files."""
        extension = file_path.suffix.lower()
        language = metadata.get("language")
        file_size = metadata.get("size", 0)

        # Configuration and important files get highest priority
        config_files = {
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".conf",
            ".dockerfile",
            ".makefile",
            ".cmake",
        }
        if extension in config_files:
            return 95

        # Important filenames
        important_names = {
            "readme",
            "license",
            "changelog",
            "authors",
            "contributors",
            "install",
            "news",
            "todo",
            "makefile",
            "dockerfile",
        }
        if file_path.name.lower() in important_names or any(
            name in file_path.name.lower() for name in important_names
        ):
            return 90

        # Code files get high priority
        if language and language in {
            "python",
            "javascript",
            "typescript",
            "java",
            "c",
            "cpp",
            "csharp",
            "php",
            "ruby",
            "go",
            "rust",
            "swift",
        }:
            return 85

        # Markup and documentation
        if extension in {".md", ".rst", ".tex", ".html", ".xml"}:
            return 75

        # Shell scripts and config
        if extension in {".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat"}:
            return 70

        # Other text files - priority based on size
        if file_size < 10 * 1024:  # < 10KB
            return 50
        elif file_size < 100 * 1024:  # < 100KB
            return 40
        elif file_size < 1024 * 1024:  # < 1MB
            return 30
        else:
            return 20

    def should_process_file(self, strategy: FileProcessingStrategy) -> bool:
        """Determine if a file should be processed based on its strategy."""
        return strategy.action != ProcessingAction.SKIP

    def get_processing_order(
        self, strategies: list[tuple[Path, FileProcessingStrategy]]
    ) -> list[tuple[Path, FileProcessingStrategy]]:
        """Sort files by processing priority (highest first)."""
        return sorted(strategies, key=lambda x: x[1].priority, reverse=True)
