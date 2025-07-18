"""Streaming file processor for handling large files efficiently."""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .file_utils import is_text_file
from .token_utils import (
    estimate_tokens_from_file,
)

logger = logging.getLogger(__name__)


class StreamingFileProcessor:
    """Processor for handling large files with streaming and chunking."""

    def __init__(
        self,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        max_workers: int = 4,
        token_estimation_method: str = "average",  # noqa: S107
    ):
        """Initialize the streaming processor.

        Args:
            max_file_size: Maximum file size to process in bytes
            max_workers: Maximum number of worker threads
            token_estimation_method: Method for token estimation
        """
        self.max_file_size = max_file_size
        self.max_workers = max_workers
        self.token_estimation_method = token_estimation_method

        # Thread-safe statistics
        self._stats_lock = threading.Lock()
        self._stats = {
            "processed_files": 0,
            "skipped_files": 0,
            "error_files": 0,
            "total_estimated_tokens": 0,
        }

    def process_file(self, file_path: Path) -> dict[str, str | list[str]]:
        """Process a single file with streaming and chunking.

        Args:
            file_path: Path to the file to process

        Returns:
            Dictionary with file content, either as string or list of chunks
        """
        try:
            file_size = file_path.stat().st_size

            # Skip files that are too large
            if file_size > self.max_file_size:
                with self._stats_lock:
                    self._stats["skipped_files"] += 1
                return {
                    "status": "skipped",
                    "reason": f"File too large: {file_size} bytes",
                    "content": "",
                }

            # Check if file is text
            if not is_text_file(file_path):
                with self._stats_lock:
                    self._stats["skipped_files"] += 1
                return {
                    "status": "skipped",
                    "reason": "Not a text file",
                    "content": "",
                }

            # Estimate tokens
            estimated_tokens = estimate_tokens_from_file(
                file_path, self.token_estimation_method
            )

            with self._stats_lock:
                self._stats["total_estimated_tokens"] += estimated_tokens

            # Read file content
            content = self._read_file_content(file_path)
            if content is not None:
                with self._stats_lock:
                    self._stats["processed_files"] += 1

                return {
                    "status": "processed",
                    "content": content,
                    "estimated_tokens": str(estimated_tokens),
                }
            else:
                with self._stats_lock:
                    self._stats["error_files"] += 1
                return {
                    "status": "error",
                    "reason": "Failed to read file",
                    "content": "",
                }

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            with self._stats_lock:
                self._stats["error_files"] += 1

            return {
                "status": "error",
                "reason": str(e),
                "content": "",
            }

    def process_files_parallel(self, file_paths: list[Path]) -> dict[str, dict]:
        """Process multiple files in parallel.

        Args:
            file_paths: List of file paths to process

        Returns:
            Dictionary mapping file paths to processing results
        """
        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(self.process_file, file_path): file_path
                for file_path in file_paths
            }

            # Collect results as they complete
            for future in as_completed(future_to_path):
                file_path = future_to_path[future]
                try:
                    result = future.result()
                    results[str(file_path)] = result
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    results[str(file_path)] = {
                        "status": "error",
                        "reason": str(e),
                        "content": "",
                    }

        return results

    def _read_file_content(self, file_path: Path) -> str | None:
        """Read file content with encoding detection."""
        try:
            # Try different encodings
            encodings = ["utf-8", "utf-16", "latin-1", "ascii"]

            for encoding in encodings:
                try:
                    with open(file_path, encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
                except (OSError, PermissionError):
                    break

            return None
        except Exception:
            return None

    def get_stats(self) -> dict[str, int]:
        """Get processing statistics."""
        with self._stats_lock:
            return self._stats.copy()

    def reset_stats(self) -> None:
        """Reset processing statistics."""
        with self._stats_lock:
            self._stats = {
                "processed_files": 0,
                "skipped_files": 0,
                "error_files": 0,
                "total_estimated_tokens": 0,
            }


class MemoryMonitor:
    """Monitor memory usage during processing."""

    def __init__(self, max_memory_mb: int = 1024):
        """Initialize memory monitor.

        Args:
            max_memory_mb: Maximum memory usage in MB before warning
        """
        self.max_memory_mb = max_memory_mb
        self.warnings_issued = 0

    def check_memory_usage(self) -> tuple[float, bool]:
        """Check current memory usage.

        Returns:
            Tuple of (current_memory_mb, is_over_limit)
        """
        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()
            current_mb = memory_info.rss / (1024 * 1024)

            over_limit = current_mb > self.max_memory_mb

            if over_limit:
                self.warnings_issued += 1
                logger.warning(
                    f"Memory usage high: {current_mb:.1f}MB "
                    f"(limit: {self.max_memory_mb}MB)"
                )

            return current_mb, over_limit

        except ImportError:
            # psutil not available, can't monitor memory
            return 0.0, False
        except Exception as e:
            logger.debug(f"Error checking memory usage: {e}")
            return 0.0, False

    def get_memory_stats(self) -> dict[str, float | int]:
        """Get memory statistics."""
        current_mb, over_limit = self.check_memory_usage()

        return {
            "current_memory_mb": current_mb,
            "max_memory_mb": self.max_memory_mb,
            "over_limit": over_limit,
            "warnings_issued": self.warnings_issued,
        }


def optimize_file_processing_order(file_paths: list[Path]) -> list[Path]:
    """Optimize the order of file processing for better performance.

    Args:
        file_paths: List of file paths to optimize

    Returns:
        Optimized list of file paths
    """
    # Separate files by estimated processing complexity
    text_files = []
    binary_files = []
    large_files = []

    for file_path in file_paths:
        try:
            file_size = file_path.stat().st_size

            # Large files last
            if file_size > 1024 * 1024:  # 1MB
                large_files.append(file_path)
            elif is_text_file(file_path):
                text_files.append(file_path)
            else:
                binary_files.append(file_path)
        except (OSError, PermissionError):
            binary_files.append(file_path)

    # Sort each category by size (smaller first)
    text_files.sort(key=lambda p: p.stat().st_size if p.exists() else 0)
    binary_files.sort(key=lambda p: p.stat().st_size if p.exists() else 0)
    large_files.sort(key=lambda p: p.stat().st_size if p.exists() else 0)

    # Return optimized order: text files first, then binary, then large
    return text_files + binary_files + large_files
