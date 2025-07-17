"""Token counting and streaming utilities for LLM workflows."""

import re
from collections.abc import Generator, Iterator
from pathlib import Path

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

# Character to token ratio estimates (rough approximations)
# Based on typical English text patterns
CHAR_TO_TOKEN_RATIO = {
    "conservative": 3.0,  # More conservative estimate
    "average": 4.0,  # Average estimate
    "optimistic": 5.0,  # More optimistic estimate
}


def estimate_tokens_from_text(text: str, method: str = "average") -> int:
    """Estimate token count from text using character-based approximation.

    Args:
        text: The text to estimate tokens for
        method: Estimation method ('conservative', 'average', 'optimistic')

    Returns:
        Estimated token count
    """
    if not text:
        return 0

    char_count = len(text)
    ratio = CHAR_TO_TOKEN_RATIO.get(method, CHAR_TO_TOKEN_RATIO["average"])

    # Adjust for code vs natural language
    # Code typically has more tokens per character
    if _is_likely_code(text):
        ratio *= 0.8  # Code has more tokens per character

    return int(char_count / ratio)


def estimate_tokens_from_file(file_path: Path, method: str = "average") -> int:
    """Estimate token count from a file without loading entire content.

    Args:
        file_path: Path to the file
        method: Estimation method ('conservative', 'average', 'optimistic')

    Returns:
        Estimated token count
    """
    try:
        file_size = file_path.stat().st_size

        # Handle empty files
        if file_size == 0:
            return 0

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
    return code_lines / len(lines) > 0.3 if lines else False


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


def chunk_text_by_tokens(
    text: str, max_tokens: int, method: str = "average"
) -> Iterator[str]:
    """Split text into chunks that fit within token limits.

    Args:
        text: Text to chunk
        max_tokens: Maximum tokens per chunk
        method: Token estimation method

    Yields:
        Text chunks that fit within the token limit
    """
    if not text:
        return

    # Estimate tokens for the entire text
    total_tokens = estimate_tokens_from_text(text, method)

    if total_tokens <= max_tokens:
        yield text
        return

    # Split by paragraphs first, then by sentences if needed
    paragraphs = text.split("\n\n")
    current_chunk = ""
    current_tokens = 0

    for paragraph in paragraphs:
        paragraph_tokens = estimate_tokens_from_text(paragraph, method)

        # If paragraph alone exceeds limit, split by sentences
        if paragraph_tokens > max_tokens:
            # Yield current chunk if it has content
            if current_chunk:
                yield current_chunk
                current_chunk = ""
                current_tokens = 0

            # Split paragraph by sentences
            sentences = re.split(r"[.!?]+", paragraph)

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                sentence_tokens = estimate_tokens_from_text(sentence, method)

                if current_tokens + sentence_tokens > max_tokens:
                    if current_chunk:
                        yield current_chunk
                        current_chunk = sentence
                        current_tokens = sentence_tokens
                    else:
                        # Single sentence too long, split by words
                        words = sentence.split()
                        word_chunk = ""

                        for word in words:
                            word_tokens = estimate_tokens_from_text(word, method)

                            if current_tokens + word_tokens > max_tokens:
                                if word_chunk:
                                    yield word_chunk
                                    word_chunk = word
                                    current_tokens = word_tokens
                                else:
                                    # Single word too long, just yield it
                                    yield word
                                    current_tokens = 0
                            else:
                                word_chunk += " " + word if word_chunk else word
                                current_tokens += word_tokens

                        if word_chunk:
                            current_chunk = word_chunk
                        else:
                            current_chunk = ""
                            current_tokens = 0
                else:
                    current_chunk += "\n" + sentence if current_chunk else sentence
                    current_tokens += sentence_tokens
        else:
            # Check if adding this paragraph would exceed limit
            if current_tokens + paragraph_tokens > max_tokens:
                if current_chunk:
                    yield current_chunk
                current_chunk = paragraph
                current_tokens = paragraph_tokens
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
                current_tokens += paragraph_tokens

    # Yield final chunk
    if current_chunk:
        yield current_chunk


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
    file_paths: list[Path], method: str = "average"
) -> dict[str, int]:
    """Calculate processing statistics for a list of files.

    Args:
        file_paths: List of file paths to analyze
        method: Token estimation method

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
                tokens = estimate_tokens_from_file(file_path, method)
                stats["total_estimated_tokens"] += tokens
                stats["total_chars"] += file_size
            else:
                stats["binary_files"] += 1
        except (OSError, PermissionError):
            continue

    return stats
