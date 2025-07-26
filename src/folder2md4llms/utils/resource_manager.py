"""Resource management utilities for folder2md4llms."""

import logging
import threading
from contextlib import contextmanager
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class ResourceError(Exception):
    """Exception raised when resource limits are exceeded."""

    pass


class ResourceManager:
    """Manage system resources during processing."""

    def __init__(self, max_memory_mb: int = 1024, max_file_handles: int = 1000):
        """Initialize resource manager.

        Args:
            max_memory_mb: Maximum memory usage in MB
            max_file_handles: Maximum number of concurrent file handles
        """
        self.max_memory_mb = max_memory_mb
        self.max_file_handles = max_file_handles
        self._lock = threading.Lock()
        self._open_files = 0
        self._initial_memory = self._get_memory_usage()

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            return float(psutil.Process().memory_info().rss / 1024 / 1024)
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return 0.0

    @contextmanager
    def file_handle(self):
        """Context manager for file handle tracking.

        Raises:
            ResourceError: If too many files are open
        """
        with self._lock:
            if self._open_files >= self.max_file_handles:
                raise ResourceError(
                    f"Too many open files: {self._open_files} >= {self.max_file_handles}"
                )
            self._open_files += 1

        try:
            yield
        finally:
            with self._lock:
                self._open_files -= 1

    def check_memory_limit(self) -> tuple[float, bool]:
        """Check if we're within memory limits.

        Returns:
            Tuple of (current_memory_mb, is_over_limit)
        """
        current_mb = self._get_memory_usage()
        over_limit = current_mb > self.max_memory_mb

        if over_limit:
            logger.warning(
                f"Memory limit exceeded: {current_mb:.1f}MB > {self.max_memory_mb}MB"
            )

        return current_mb, over_limit

    def get_resource_stats(self) -> dict[str, Any]:
        """Get current resource usage statistics.

        Returns:
            Dictionary with resource usage stats
        """
        current_memory = self._get_memory_usage()

        return {
            "memory_mb": current_memory,
            "memory_increase_mb": current_memory - self._initial_memory,
            "memory_percent": (current_memory / self.max_memory_mb) * 100,
            "open_files": self._open_files,
            "file_handles_percent": (self._open_files / self.max_file_handles) * 100,
        }

    @contextmanager
    def monitor_operation(self, operation_name: str):
        """Monitor resource usage during an operation.

        Args:
            operation_name: Name of the operation being monitored
        """
        start_memory = self._get_memory_usage()

        try:
            yield
        finally:
            end_memory = self._get_memory_usage()
            memory_delta = end_memory - start_memory

            if memory_delta > 50:  # Log if operation used more than 50MB
                logger.info(
                    f"Operation '{operation_name}' used {memory_delta:.1f}MB of memory"
                )

            # Check if we're approaching limits
            if end_memory > self.max_memory_mb * 0.9:
                logger.warning(
                    f"Memory usage at 90% of limit after '{operation_name}': "
                    f"{end_memory:.1f}MB / {self.max_memory_mb}MB"
                )
