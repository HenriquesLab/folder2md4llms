"""Token counting and streaming utilities for LLM workflows."""

import hashlib
import logging
import re
from collections.abc import Generator
from pathlib import Path

# Optional tiktoken import for accurate token counting
try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

logger = logging.getLogger(__name__)

# Token estimation constants for different models
MODEL_TOKEN_LIMITS = {
    "gpt-3.5-turbo": 4096,
    "gpt-4": 8192,
    "gpt-4-turbo": 128000,
    "gpt-4o": 128000,
    "claude-3-sonnet": 200000,
    "claude-3-opus": 200000,
    "claude-3-haiku": 200000,
    "claude-3.5-sonnet": 200000,
    "gemini-1.5-pro": 2000000,
    "gemini-1.5-flash": 1000000,
}

# Model to tiktoken encoding mapping
MODEL_TO_ENCODING = {
    "gpt-3.5-turbo": "cl100k_base",
    "gpt-4": "cl100k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-4o": "o200k_base",
    "text-davinci-003": "p50k_base",
    "text-davinci-002": "p50k_base",
    "text-davinci-001": "r50k_base",
    "davinci": "r50k_base",
    "curie": "r50k_base",
    "babbage": "r50k_base",
    "ada": "r50k_base",
}

# Character to token ratio estimates (rough approximations)
# Based on typical English text patterns
CHAR_TO_TOKEN_RATIO = {
    "conservative": 3.0,  # More conservative estimate
    "average": 4.0,  # Average estimate
    "optimistic": 5.0,  # More optimistic estimate
}


def is_tiktoken_available() -> bool:
    """Check if tiktoken is available for accurate token counting.

    Returns:
        True if tiktoken is available, False otherwise
    """
    return TIKTOKEN_AVAILABLE


def get_token_counting_method_info(method: str) -> dict[str, str]:
    """Get information about the token counting method.

    Args:
        method: Token estimation method

    Returns:
        Dictionary with method information
    """
    info = {
        "method": method,
        "accurate": "false",
        "description": "Character-based estimation",
        "recommendation": "",
    }

    if method == "tiktoken":
        if TIKTOKEN_AVAILABLE:
            info.update(
                {
                    "accurate": "true",
                    "description": "Precise token counting using tiktoken",
                    "recommendation": "Most accurate for OpenAI models",
                }
            )
        else:
            info.update(
                {
                    "accurate": "false",
                    "description": "tiktoken not available, falling back to character-based",
                    "recommendation": "Install tiktoken for accurate counting: pip install tiktoken",
                }
            )
    elif method in ["conservative", "average", "optimistic"]:
        info.update(
            {
                "description": f"Character-based estimation ({method})",
                "recommendation": "For better accuracy, install tiktoken: pip install tiktoken",
            }
        )

    return info


def get_tiktoken_encoding(model_name: str = "gpt-4") -> str:
    """Get the tiktoken encoding name for a model.

    Args:
        model_name: Name of the model

    Returns:
        Encoding name for tiktoken
    """
    # Try exact match first
    if model_name in MODEL_TO_ENCODING:
        return MODEL_TO_ENCODING[model_name]

    # Try partial matching for model variants
    for model_key, encoding in MODEL_TO_ENCODING.items():
        if model_key in model_name.lower():
            return encoding

    # Default to cl100k_base (GPT-4 family)
    return "cl100k_base"


def count_tokens_tiktoken(text: str, model_name: str = "gpt-4") -> int:
    """Count tokens using tiktoken (accurate for OpenAI models).

    Args:
        text: The text to count tokens for
        model_name: Name of the model to use encoding for

    Returns:
        Exact token count
    """
    if not TIKTOKEN_AVAILABLE:
        raise ImportError(
            "tiktoken is not available. Install with: pip install tiktoken"
        )

    if not text:
        return 0

    try:
        encoding_name = get_tiktoken_encoding(model_name)
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Failed to count tokens with tiktoken: {e}")
        # Fall back to character-based estimation
        return estimate_tokens_from_text(text, "average")


def estimate_tokens_from_text(
    text: str, method: str = "average", model_name: str | None = None
) -> int:
    """Estimate token count from text using tiktoken when available, fallback to character-based approximation.

    Args:
        text: The text to estimate tokens for
        method: Estimation method ('conservative', 'average', 'optimistic', 'tiktoken')
        model_name: Model name for tiktoken encoding (only used with tiktoken)

    Returns:
        Estimated or exact token count
    """
    if not text:
        return 0

    # Use tiktoken if available and requested (or if method is 'tiktoken')
    if TIKTOKEN_AVAILABLE and (method == "tiktoken" or model_name is not None):
        try:
            return count_tokens_tiktoken(text, model_name or "gpt-4")
        except Exception as e:
            logger.warning(f"tiktoken failed, falling back to character-based: {e}")
            # Fall through to character-based estimation

    # Character-based estimation fallback
    char_count = len(text)
    ratio = CHAR_TO_TOKEN_RATIO.get(method, CHAR_TO_TOKEN_RATIO["average"])

    # Adjust for code vs natural language
    # Code typically has more tokens per character
    if _is_likely_code(text):
        ratio *= 0.8  # Code has more tokens per character

    # Ensure ratio is never zero or negative
    if ratio <= 0:
        ratio = CHAR_TO_TOKEN_RATIO["average"]

    return int(char_count / ratio)


def estimate_tokens_from_file(
    file_path: Path, method: str = "average", model_name: str | None = None
) -> int:
    """Estimate token count from a file without loading entire content.

    Args:
        file_path: Path to the file
        method: Estimation method ('conservative', 'average', 'optimistic', 'tiktoken')
        model_name: Model name for tiktoken encoding (only used with tiktoken)

    Returns:
        Estimated or exact token count
    """
    try:
        file_size = file_path.stat().st_size

        # Handle empty files
        if file_size == 0:
            return 0

        # For tiktoken, we need actual text content for accurate counting
        # Sample a larger portion for tiktoken to get better estimates
        if TIKTOKEN_AVAILABLE and (method == "tiktoken" or model_name is not None):
            try:
                # Sample up to 32KB for tiktoken analysis
                sample_size = min(32768, file_size)

                with open(file_path, "rb") as f:
                    sample_bytes = f.read(sample_size)

                # Try to decode sample
                sample_text = sample_bytes.decode("utf-8")

                # Count tokens in sample
                sample_tokens = count_tokens_tiktoken(
                    sample_text, model_name or "gpt-4"
                )

                # Extrapolate to full file size
                if len(sample_bytes) > 0:
                    tokens_per_byte = sample_tokens / len(sample_bytes)
                    return int(file_size * tokens_per_byte)
                else:
                    return 0

            except UnicodeDecodeError:
                # Binary file, fall back to rough estimation
                return file_size // 10
            except Exception as e:
                logger.warning(f"tiktoken file estimation failed: {e}")
                # Fall through to character-based estimation

        # Character-based estimation (original logic)
        # Sample first few KB to get character distribution
        sample_size = min(4096, file_size)

        with open(file_path, "rb") as f:
            sample_bytes = f.read(sample_size)

        # Try to decode sample to estimate character count
        try:
            sample_text = sample_bytes.decode("utf-8")
            # Avoid division by zero for empty samples
            if len(sample_bytes) == 0:
                return 0
            chars_per_byte = len(sample_text) / len(sample_bytes)
        except UnicodeDecodeError:
            # Binary file, estimate very roughly
            return file_size // 10  # Very rough estimate for binary

        # Estimate total character count
        total_chars = int(file_size * chars_per_byte)

        # Convert to tokens
        ratio = CHAR_TO_TOKEN_RATIO.get(method, CHAR_TO_TOKEN_RATIO["average"])

        # Adjust for likely code content
        if _is_likely_code_file(file_path):
            ratio *= 0.8

        # Ensure ratio is never zero or negative
        if ratio <= 0:
            ratio = CHAR_TO_TOKEN_RATIO["average"]

        return int(total_chars / ratio)

    except (OSError, PermissionError):
        return 0


def _is_likely_code(text: str) -> bool:
    """Check if text looks like code based on patterns."""
    # Simple heuristics for code detection
    code_indicators = [
        r"^\s*import\s+",  # Import statements
        r"^\s*from\s+\w+\s+import",  # From imports
        r"^\s*def\s+\w+\s*\(",  # Function definitions
        r"^\s*class\s+\w+",  # Class definitions
        r"^\s*if\s+.*:",  # If statements
        r"^\s*for\s+.*:",  # For loops
        r"^\s*while\s+.*:",  # While loops
        r"^\s*#.*",  # Comments
        r"^\s*//.*",  # C-style comments
        r"^\s*/\*.*\*/",  # C-style block comments
        r"[\{\}\[\]();]",  # Common code punctuation
    ]

    # Count lines that match code patterns
    lines = text.split("\n")[:50]  # Check first 50 lines
    code_lines = 0

    for line in lines:
        for pattern in code_indicators:
            if re.search(pattern, line, re.MULTILINE):
                code_lines += 1
                break

    # If more than 30% of lines look like code, consider it code
    return (code_lines / len(lines) > 0.3) if lines else False


def _is_likely_code_file(file_path: Path) -> bool:
    """Check if file is likely code based on extension."""
    code_extensions = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".java",
        ".c",
        ".cpp",
        ".cc",
        ".cxx",
        ".h",
        ".hpp",
        ".cs",
        ".php",
        ".rb",
        ".go",
        ".rs",
        ".swift",
        ".kt",
        ".scala",
        ".r",
        ".m",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".ps1",
        ".bat",
        ".cmd",
        ".html",
        ".htm",
        ".css",
        ".scss",
        ".sass",
        ".less",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".xml",
        ".sql",
        ".dockerfile",
        ".makefile",
        ".cmake",
        ".gradle",
        ".vim",
        ".lua",
        ".pl",
        ".pm",
        ".clj",
        ".cljs",
        ".elm",
        ".ex",
        ".exs",
        ".erl",
        ".hrl",
        ".hs",
        ".lhs",
        ".ml",
        ".mli",
        ".fs",
        ".fsi",
        ".fsx",
        ".dart",
        ".proto",
        ".thrift",
        ".graphql",
        ".gql",
    }

    return file_path.suffix.lower() in code_extensions


def stream_file_content(
    file_path: Path, chunk_size: int = 8192
) -> Generator[str, None, None]:
    """Stream file content in chunks to reduce memory usage.

    Args:
        file_path: Path to the file to stream
        chunk_size: Size of each chunk in bytes

    Yields:
        String chunks of the file content
    """
    try:
        # Try different encodings
        encodings = ["utf-8", "utf-16", "latin-1", "ascii"]

        for encoding in encodings:
            try:
                with open(file_path, encoding=encoding) as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
                break
            except UnicodeDecodeError:
                continue
            except (OSError, PermissionError):
                break
    except Exception:
        # If all fails, return empty generator
        return


def get_model_token_limit(model_name: str) -> int:
    """Get the token limit for a specific model.

    Args:
        model_name: Name of the model

    Returns:
        Token limit for the model, or default if unknown
    """
    # Try exact match first
    if model_name in MODEL_TOKEN_LIMITS:
        return MODEL_TOKEN_LIMITS[model_name]

    # Try partial matching for model variants
    for model_key in MODEL_TOKEN_LIMITS:
        if model_key in model_name.lower():
            return MODEL_TOKEN_LIMITS[model_key]

    # Default to a conservative limit
    return 4096


def calculate_processing_stats(
    file_paths: list[Path], method: str = "average", model_name: str | None = None
) -> dict[str, int]:
    """Calculate processing statistics for a list of files.

    Args:
        file_paths: List of file paths to analyze
        method: Token estimation method
        model_name: Model name for tiktoken encoding (only used with tiktoken)

    Returns:
        Dictionary with processing statistics
    """
    stats = {
        "total_files": len(file_paths),
        "total_estimated_tokens": 0,
        "total_chars": 0,
        "text_files": 0,
        "binary_files": 0,
    }

    for file_path in file_paths:
        try:
            file_size = file_path.stat().st_size

            # Check if text file
            if _is_likely_code_file(file_path) or file_path.suffix.lower() in [
                ".txt",
                ".md",
                ".rst",
            ]:
                stats["text_files"] += 1
                tokens = estimate_tokens_from_file(file_path, method, model_name)
                stats["total_estimated_tokens"] += tokens
                stats["total_chars"] += file_size
            else:
                stats["binary_files"] += 1
        except (OSError, PermissionError):
            continue

    return stats


class CachedTokenCounter:
    """Token counter with caching for improved performance."""

    def __init__(self, method: str = "tiktoken", model: str = "gpt-4"):
        """Initialize the cached token counter.

        Args:
            method: Token counting method ('tiktoken', 'average', 'conservative', 'optimistic')
            model: Model name for tiktoken encoding
        """
        self.method = method
        self.model = model
        self._cache: dict[str, int] = {}
        self._encoding = None

        # Initialize tiktoken encoding if available and method is tiktoken
        if self.method == "tiktoken" and TIKTOKEN_AVAILABLE:
            self._encoding = get_tiktoken_encoding(model)

    def _count_tokens_cached(self, text_hash: str, text_len: int) -> int:
        """Count tokens with caching based on text hash.

        Args:
            text_hash: MD5 hash of the text
            text_len: Length of the text (for cache key)

        Returns:
            Number of tokens
        """
        # This is called with the actual text from the wrapper
        # The actual counting logic is in count_tokens
        return 0  # Placeholder, actual counting done in count_tokens

    def count_tokens(self, text: str) -> int:
        """Count tokens with caching.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        # Create a hash of the text for caching (not for security purposes)
        text_hash = hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()

        # Check cache first
        cache_key = f"{text_hash}:{len(text)}"
        if cache_key in self._cache:
            return int(self._cache[cache_key])

        # Count tokens based on method
        if self.method == "tiktoken" and self._encoding:
            try:
                token_count = len(self._encoding.encode(text))
            except Exception as e:
                logger.warning(
                    f"Tiktoken encoding failed: {e}, falling back to average method"
                )
                token_count = self._estimate_tokens_average(text)
        elif self.method == "conservative":
            token_count = self._estimate_tokens_conservative(text)
        elif self.method == "optimistic":
            token_count = self._estimate_tokens_optimistic(text)
        else:  # average or fallback
            token_count = self._estimate_tokens_average(text)

        # Cache the result
        self._cache[cache_key] = token_count

        # Limit cache size
        if len(self._cache) > 10000:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self._cache.keys())[:1000]
            for key in keys_to_remove:
                del self._cache[key]

        return token_count

    def _estimate_tokens_average(self, text: str) -> int:
        """Estimate tokens using average method."""
        # Check if content looks like code
        is_code = _is_likely_code(text)

        if is_code:
            # Code typically has more tokens per character
            return int(len(text) / 3.5)
        else:
            # Regular text
            return int(len(text) / 4.0)

    def _estimate_tokens_conservative(self, text: str) -> int:
        """Estimate tokens using conservative method."""
        return int(len(text) / 3.0)

    def _estimate_tokens_optimistic(self, text: str) -> int:
        """Estimate tokens using optimistic method."""
        return int(len(text) / 5.0)

    def clear_cache(self):
        """Clear the token cache."""
        self._cache.clear()

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "cache_size": len(self._cache),
            "method": self.method,
            "model": self.model,
            "tiktoken_available": TIKTOKEN_AVAILABLE and self._encoding is not None,
        }
