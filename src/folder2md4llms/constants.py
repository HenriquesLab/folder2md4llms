"""Constants used throughout folder2md4llms.

This module defines constants to avoid hardcoding values across multiple files.
"""

# File size constants (in bytes)
DEFAULT_MAX_FILE_SIZE = (
    100 * 1024 * 1024
)  # 100MB - default maximum file size to process
BINARY_ANALYSIS_SIZE_LIMIT = (
    1 * 1024 * 1024
)  # 1MB - maximum size for binary file analysis
CHUNKED_READ_THRESHOLD = 1 * 1024 * 1024  # 1MB - threshold for chunked file reading

# Memory constants
DEFAULT_MAX_MEMORY_MB = 1024  # 1GB - default maximum memory usage

# Token/character constants
DEFAULT_TOKEN_LIMIT = 100000  # Default token limit when none specified
DEFAULT_CHAR_LIMIT = None  # No character limit by default

# Performance constants
DEFAULT_MAX_WORKERS = 4  # Default number of parallel workers
DEFAULT_UPDATE_CHECK_INTERVAL = 24 * 60 * 60  # 24 hours in seconds

# Size conversion constants
BYTES_PER_KB = 1024
BYTES_PER_MB = 1024 * 1024
BYTES_PER_GB = 1024 * 1024 * 1024
