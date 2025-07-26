"""Logging configuration for folder2md4llms."""

import logging
import sys
from pathlib import Path
from typing import Any


def setup_logging(
    verbose: bool = False, log_file: Path | None = None, log_level: str = "INFO"
) -> None:
    """Configure logging with proper formatters and handlers.

    Args:
        verbose: Enable verbose logging
        log_file: Optional file to write logs to
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Map string levels to logging constants
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    # Determine effective log level
    if verbose:
        effective_level = logging.DEBUG
    else:
        effective_level = level_map.get(log_level.upper(), logging.INFO)

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    simple_formatter = logging.Formatter("%(levelname)s: %(message)s")

    # Remove existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        simple_formatter if not verbose else detailed_formatter
    )
    console_handler.setLevel(effective_level)

    # Add console handler
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        try:
            # Ensure log directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
            file_handler.setFormatter(detailed_formatter)
            file_handler.setLevel(logging.DEBUG)  # Always log everything to file
            root_logger.addHandler(file_handler)
        except Exception as e:
            logging.warning(f"Failed to create log file {log_file}: {e}")

    # Set root logger level
    root_logger.setLevel(logging.DEBUG)

    # Configure specific loggers
    folder2md_logger = logging.getLogger("folder2md4llms")
    folder2md_logger.setLevel(effective_level)

    # Reduce noise from third-party libraries
    for noisy_logger in ["urllib3", "httpx", "PIL", "pypdf"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


class LogContext:
    """Context manager for temporary logging configuration changes."""

    def __init__(self, **kwargs: Any):
        """Initialize log context.

        Args:
            **kwargs: Logging configuration options (verbose, log_file, log_level)
        """
        self.kwargs = kwargs
        self.original_handlers: list[logging.Handler] = []
        self.original_levels: dict[str, int] = {}

    def __enter__(self):
        """Enter the context and save current logging state."""
        root_logger = logging.getLogger()

        # Save current handlers
        self.original_handlers = root_logger.handlers[:]

        # Save current levels
        self.original_levels["root"] = root_logger.level
        self.original_levels["folder2md4llms"] = logging.getLogger(
            "folder2md4llms"
        ).level

        # Apply new configuration
        setup_logging(**self.kwargs)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original logging configuration."""
        root_logger = logging.getLogger()

        # Remove handlers added by our setup
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Restore original handlers
        for handler in self.original_handlers:
            root_logger.addHandler(handler)

        # Restore original levels
        root_logger.setLevel(self.original_levels.get("root", logging.WARNING))
        logging.getLogger("folder2md4llms").setLevel(
            self.original_levels.get("folder2md4llms", logging.WARNING)
        )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the appropriate name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
