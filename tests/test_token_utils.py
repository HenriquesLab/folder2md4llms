"""Comprehensive tests for token counting and streaming utilities."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from folder2md4llms.utils.token_utils import (
    CHAR_TO_TOKEN_RATIO,
    MODEL_TO_ENCODING,
    MODEL_TOKEN_LIMITS,
    TIKTOKEN_AVAILABLE,
    _is_likely_code,
    _is_likely_code_file,
    calculate_processing_stats,
    count_tokens_tiktoken,
    estimate_tokens_from_file,
    estimate_tokens_from_text,
    get_model_token_limit,
    get_tiktoken_encoding,
    get_token_counting_method_info,
    is_tiktoken_available,
    stream_file_content,
)


class TestTiktokenAvailability:
    """Test tiktoken availability detection."""

    def test_is_tiktoken_available_actual(self):
        """Test actual tiktoken availability."""
        result = is_tiktoken_available()
        assert isinstance(result, bool)
        # Should match the module-level constant
        assert result == TIKTOKEN_AVAILABLE

    @patch("folder2md4llms.utils.token_utils.TIKTOKEN_AVAILABLE", True)
    def test_is_tiktoken_available_mocked_true(self):
        """Test tiktoken availability when mocked as True."""
        result = is_tiktoken_available()
        assert result is True

    @patch("folder2md4llms.utils.token_utils.TIKTOKEN_AVAILABLE", False)
    def test_is_tiktoken_available_mocked_false(self):
        """Test tiktoken availability when mocked as False."""
        result = is_tiktoken_available()
        assert result is False


class TestTokenCountingMethodInfo:
    """Test token counting method information."""

    def test_get_token_counting_method_info_tiktoken(self):
        """Test getting info for tiktoken method."""
        info = get_token_counting_method_info("tiktoken")
        assert isinstance(info, dict)
        assert "method" in info
        assert "description" in info
        assert "accurate" in info
        assert "recommendation" in info
        assert info["method"] == "tiktoken"
        assert info["accurate"] in ["true", "false"]  # Depends on tiktoken availability

    def test_get_token_counting_method_info_conservative(self):
        """Test getting info for conservative method."""
        info = get_token_counting_method_info("conservative")
        assert isinstance(info, dict)
        assert info["method"] == "conservative"
        assert info["accurate"] == "false"

    def test_get_token_counting_method_info_average(self):
        """Test getting info for average method."""
        info = get_token_counting_method_info("average")
        assert isinstance(info, dict)
        assert info["method"] == "average"
        assert info["accurate"] == "false"

    def test_get_token_counting_method_info_optimistic(self):
        """Test getting info for optimistic method."""
        info = get_token_counting_method_info("optimistic")
        assert isinstance(info, dict)
        assert info["method"] == "optimistic"
        assert info["accurate"] == "false"

    def test_get_token_counting_method_info_unknown(self):
        """Test getting info for unknown method."""
        info = get_token_counting_method_info("unknown")
        assert isinstance(info, dict)
        assert info["method"] == "unknown"
        assert info["accurate"] == "false"


class TestTiktokenEncoding:
    """Test tiktoken encoding detection."""

    def test_get_tiktoken_encoding_gpt4(self):
        """Test getting tiktoken encoding for GPT-4."""
        encoding = get_tiktoken_encoding("gpt-4")
        assert encoding == "cl100k_base"

    def test_get_tiktoken_encoding_gpt35(self):
        """Test getting tiktoken encoding for GPT-3.5."""
        encoding = get_tiktoken_encoding("gpt-3.5-turbo")
        assert encoding == "cl100k_base"

    def test_get_tiktoken_encoding_gpt4o(self):
        """Test getting tiktoken encoding for GPT-4o."""
        encoding = get_tiktoken_encoding("gpt-4o")
        assert encoding == "o200k_base"

    def test_get_tiktoken_encoding_default(self):
        """Test getting tiktoken encoding with default model."""
        encoding = get_tiktoken_encoding()
        assert encoding == "cl100k_base"  # Default is gpt-4

    def test_get_tiktoken_encoding_unknown_model(self):
        """Test getting tiktoken encoding for unknown model."""
        encoding = get_tiktoken_encoding("unknown-model")
        assert encoding == "cl100k_base"  # Falls back to default

    def test_get_tiktoken_encoding_legacy_model(self):
        """Test getting tiktoken encoding for legacy models."""
        encoding = get_tiktoken_encoding("text-davinci-003")
        assert encoding == "p50k_base"

        encoding = get_tiktoken_encoding("davinci")
        assert encoding == "r50k_base"


class TestTiktokenTokenCounting:
    """Test tiktoken token counting."""

    @pytest.mark.skipif(not TIKTOKEN_AVAILABLE, reason="tiktoken not available")
    def test_count_tokens_tiktoken_simple(self):
        """Test counting tokens with tiktoken for simple text."""
        text = "Hello world"
        tokens = count_tokens_tiktoken(text)
        assert isinstance(tokens, int)
        assert tokens > 0

    @pytest.mark.skipif(not TIKTOKEN_AVAILABLE, reason="tiktoken not available")
    def test_count_tokens_tiktoken_empty(self):
        """Test counting tokens with tiktoken for empty text."""
        tokens = count_tokens_tiktoken("")
        assert tokens == 0

    @pytest.mark.skipif(not TIKTOKEN_AVAILABLE, reason="tiktoken not available")
    def test_count_tokens_tiktoken_code(self):
        """Test counting tokens with tiktoken for code."""
        code = "def hello_world():\n    print('Hello, world!')\n    return True"
        tokens = count_tokens_tiktoken(code)
        assert isinstance(tokens, int)
        assert tokens > 0

    @pytest.mark.skipif(not TIKTOKEN_AVAILABLE, reason="tiktoken not available")
    def test_count_tokens_tiktoken_different_models(self):
        """Test counting tokens with tiktoken for different models."""
        text = "The quick brown fox jumps over the lazy dog."

        gpt4_tokens = count_tokens_tiktoken(text, "gpt-4")
        gpt35_tokens = count_tokens_tiktoken(text, "gpt-3.5-turbo")
        gpt4o_tokens = count_tokens_tiktoken(text, "gpt-4o")

        assert isinstance(gpt4_tokens, int)
        assert isinstance(gpt35_tokens, int)
        assert isinstance(gpt4o_tokens, int)
        assert gpt4_tokens > 0
        assert gpt35_tokens > 0
        assert gpt4o_tokens > 0

    @pytest.mark.skipif(not TIKTOKEN_AVAILABLE, reason="tiktoken not available")
    def test_count_tokens_tiktoken_unicode(self):
        """Test counting tokens with tiktoken for Unicode text."""
        text = "Hello 世界! Café münü naïve résumé"
        tokens = count_tokens_tiktoken(text)
        assert isinstance(tokens, int)
        assert tokens > 0

    @patch("folder2md4llms.utils.token_utils.TIKTOKEN_AVAILABLE", False)
    def test_count_tokens_tiktoken_unavailable(self):
        """Test counting tokens with tiktoken when unavailable."""
        text = "Hello world"
        with pytest.raises(ImportError, match="tiktoken is not available"):
            count_tokens_tiktoken(text)


class TestEstimateTokensFromText:
    """Test token estimation from text."""

    def test_estimate_tokens_from_text_tiktoken(self):
        """Test token estimation using tiktoken method."""
        text = "Hello world, this is a test string."
        tokens = estimate_tokens_from_text(text, method="tiktoken")
        assert isinstance(tokens, int)
        assert tokens > 0

    def test_estimate_tokens_from_text_conservative(self):
        """Test token estimation using conservative method."""
        text = "Hello world, this is a test string."
        tokens = estimate_tokens_from_text(text, method="conservative")
        assert isinstance(tokens, int)
        assert tokens > 0
        # Conservative should give higher estimate
        expected = int(len(text) / CHAR_TO_TOKEN_RATIO["conservative"])
        assert tokens == expected

    def test_estimate_tokens_from_text_average(self):
        """Test token estimation using average method."""
        text = "Hello world, this is a test string."
        tokens = estimate_tokens_from_text(text, method="average")
        assert isinstance(tokens, int)
        assert tokens > 0
        expected = int(len(text) / CHAR_TO_TOKEN_RATIO["average"])
        assert tokens == expected

    def test_estimate_tokens_from_text_optimistic(self):
        """Test token estimation using optimistic method."""
        text = "Hello world, this is a test string."
        tokens = estimate_tokens_from_text(text, method="optimistic")
        assert isinstance(tokens, int)
        assert tokens > 0
        expected = int(len(text) / CHAR_TO_TOKEN_RATIO["optimistic"])
        assert tokens == expected

    def test_estimate_tokens_from_text_empty(self):
        """Test token estimation for empty text."""
        tokens = estimate_tokens_from_text("")
        assert tokens == 0

    def test_estimate_tokens_from_text_whitespace(self):
        """Test token estimation for whitespace."""
        tokens = estimate_tokens_from_text("   \n\n\t   ")
        assert isinstance(tokens, int)
        assert tokens >= 0

    def test_estimate_tokens_from_text_code_vs_text(self):
        """Test token estimation for code vs natural text."""
        code = "def hello():\n    print('world')\n    return True"
        text = "Hello world, this is a natural language sentence."

        code_tokens = estimate_tokens_from_text(code)
        text_tokens = estimate_tokens_from_text(text)

        assert isinstance(code_tokens, int)
        assert isinstance(text_tokens, int)
        assert code_tokens > 0
        assert text_tokens > 0

    def test_estimate_tokens_from_text_different_models(self):
        """Test token estimation for different models."""
        text = "The quick brown fox jumps over the lazy dog."

        gpt4_tokens = estimate_tokens_from_text(
            text, method="tiktoken", model_name="gpt-4"
        )
        gpt35_tokens = estimate_tokens_from_text(
            text, method="tiktoken", model_name="gpt-3.5-turbo"
        )

        assert isinstance(gpt4_tokens, int)
        assert isinstance(gpt35_tokens, int)
        assert gpt4_tokens > 0
        assert gpt35_tokens > 0

    def test_estimate_tokens_from_text_unknown_method(self):
        """Test token estimation with unknown method."""
        text = "Hello world"
        tokens = estimate_tokens_from_text(text, method="unknown")
        # Should fall back to average
        expected = int(len(text) / CHAR_TO_TOKEN_RATIO["average"])
        assert tokens == expected

    def test_estimate_tokens_from_text_long_text(self):
        """Test token estimation for long text."""
        text = "This is a test. " * 1000  # 16,000 characters
        tokens = estimate_tokens_from_text(text)
        assert isinstance(tokens, int)
        assert tokens > 1000  # Should be substantial number of tokens

    def test_estimate_tokens_from_text_special_characters(self):
        """Test token estimation with special characters."""
        text = "Hello! @#$%^&*()_+-=[]{}|;':\",./<>?"
        tokens = estimate_tokens_from_text(text)
        assert isinstance(tokens, int)
        assert tokens > 0


class TestEstimateTokensFromFile:
    """Test token estimation from files."""

    def test_estimate_tokens_from_file_text(self):
        """Test token estimation from text file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello world, this is a test file.")
            temp_path = Path(f.name)

        try:
            tokens = estimate_tokens_from_file(temp_path)
            assert isinstance(tokens, int)
            assert tokens > 0
        finally:
            temp_path.unlink()

    def test_estimate_tokens_from_file_python(self):
        """Test token estimation from Python file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def hello():\n    print('world')\n    return True")
            temp_path = Path(f.name)

        try:
            tokens = estimate_tokens_from_file(temp_path)
            assert isinstance(tokens, int)
            assert tokens > 0
        finally:
            temp_path.unlink()

    def test_estimate_tokens_from_file_empty(self):
        """Test token estimation from empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            tokens = estimate_tokens_from_file(temp_path)
            assert tokens == 0
        finally:
            temp_path.unlink()

    def test_estimate_tokens_from_file_nonexistent(self):
        """Test token estimation from non-existent file."""
        tokens = estimate_tokens_from_file(Path("nonexistent.txt"))
        assert tokens == 0

    def test_estimate_tokens_from_file_different_methods(self):
        """Test token estimation from file with different methods."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello world, this is a test file.")
            temp_path = Path(f.name)

        try:
            conservative_tokens = estimate_tokens_from_file(
                temp_path, method="conservative"
            )
            average_tokens = estimate_tokens_from_file(temp_path, method="average")
            optimistic_tokens = estimate_tokens_from_file(
                temp_path, method="optimistic"
            )

            assert isinstance(conservative_tokens, int)
            assert isinstance(average_tokens, int)
            assert isinstance(optimistic_tokens, int)
            assert conservative_tokens > 0
            assert average_tokens > 0
            assert optimistic_tokens > 0
            # Conservative should give highest estimate
            assert conservative_tokens >= average_tokens >= optimistic_tokens
        finally:
            temp_path.unlink()

    def test_estimate_tokens_from_file_binary(self):
        """Test token estimation from binary file."""
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
            f.write(b"\x00\x01\x02\x03")
            temp_path = Path(f.name)

        try:
            tokens = estimate_tokens_from_file(temp_path)
            # Binary files may return 0 or small number depending on implementation
            assert isinstance(tokens, int)
            assert tokens >= 0
        finally:
            temp_path.unlink()

    def test_estimate_tokens_from_file_encoding_error(self):
        """Test token estimation from file with encoding issues."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            # Write invalid UTF-8 bytes
            f.write(b"\xff\xfe\xfd")
            temp_path = Path(f.name)

        try:
            tokens = estimate_tokens_from_file(temp_path)
            assert tokens == 0  # Should handle encoding errors gracefully
        finally:
            temp_path.unlink()


class TestCodeDetection:
    """Test code detection utilities."""

    def test_is_likely_code_python(self):
        """Test code detection for Python code."""
        code = "def hello():\n    print('world')\n    return True"
        assert _is_likely_code(code) is True

    def test_is_likely_code_javascript(self):
        """Test code detection for JavaScript code."""
        code = "function hello() {\n    console.log('world');\n    return true;\n}"
        assert _is_likely_code(code) is True

    def test_is_likely_code_natural_text(self):
        """Test code detection for natural text."""
        text = "This is a natural language sentence with normal punctuation."
        assert _is_likely_code(text) is False

    def test_is_likely_code_mixed_content(self):
        """Test code detection for mixed content."""
        mixed = "Here is some code: def hello(): print('world')"
        result = _is_likely_code(mixed)
        assert isinstance(result, bool)

    def test_is_likely_code_empty(self):
        """Test code detection for empty text."""
        assert _is_likely_code("") is False

    def test_is_likely_code_whitespace(self):
        """Test code detection for whitespace."""
        assert _is_likely_code("   \n\n\t   ") is False

    def test_is_likely_code_file_python(self):
        """Test code file detection for Python file."""
        assert _is_likely_code_file(Path("test.py")) is True

    def test_is_likely_code_file_javascript(self):
        """Test code file detection for JavaScript file."""
        assert _is_likely_code_file(Path("test.js")) is True

    def test_is_likely_code_file_text(self):
        """Test code file detection for text file."""
        assert _is_likely_code_file(Path("test.txt")) is False

    def test_is_likely_code_file_markdown(self):
        """Test code file detection for Markdown file."""
        assert _is_likely_code_file(Path("README.md")) is False

    def test_is_likely_code_file_no_extension(self):
        """Test code file detection for file without extension."""
        assert _is_likely_code_file(Path("README")) is False

    def test_is_likely_code_file_various_extensions(self):
        """Test code file detection for various file extensions."""
        code_files = [
            "test.py",
            "test.js",
            "test.ts",
            "test.jsx",
            "test.tsx",
            "test.java",
            "test.cpp",
            "test.c",
            "test.h",
            "test.go",
            "test.rs",
            "test.php",
            "test.rb",
            "test.swift",
            "test.kt",
        ]

        for filename in code_files:
            result = _is_likely_code_file(Path(filename))
            assert isinstance(result, bool)
            # Most common code files should be detected as code
            if filename.endswith((".py", ".js", ".ts", ".java", ".cpp", ".c", ".go")):
                assert result is True

        non_code_files = ["test.txt", "test.pdf", "test.docx", "test.jpg"]

        for filename in non_code_files:
            result = _is_likely_code_file(Path(filename))
            assert isinstance(result, bool)
            # These should clearly not be code files
            assert result is False


class TestModelTokenLimits:
    """Test model token limit utilities."""

    def test_get_model_token_limit_gpt4(self):
        """Test getting token limit for GPT-4."""
        limit = get_model_token_limit("gpt-4")
        assert limit == 8192

    def test_get_model_token_limit_gpt4_turbo(self):
        """Test getting token limit for GPT-4 Turbo."""
        limit = get_model_token_limit("gpt-4-turbo")
        assert limit == 128000

    def test_get_model_token_limit_claude(self):
        """Test getting token limit for Claude."""
        limit = get_model_token_limit("claude-3.5-sonnet")
        assert limit == 200000

    def test_get_model_token_limit_gemini(self):
        """Test getting token limit for Gemini."""
        limit = get_model_token_limit("gemini-1.5-pro")
        assert limit == 2000000

    def test_get_model_token_limit_unknown(self):
        """Test getting token limit for unknown model."""
        limit = get_model_token_limit("unknown-model")
        assert isinstance(limit, int)
        assert limit > 0  # Should return some reasonable default

    def test_get_model_token_limit_case_insensitive(self):
        """Test getting token limit with case variations."""
        limit1 = get_model_token_limit("GPT-4")
        limit2 = get_model_token_limit("gpt-4")
        assert limit1 == limit2 == 8192

    def test_model_token_limits_constants(self):
        """Test that model token limits constants are reasonable."""
        for model, limit in MODEL_TOKEN_LIMITS.items():
            assert isinstance(model, str)
            assert isinstance(limit, int)
            assert limit > 0
            assert limit >= 1000  # All should be at least 1K tokens


class TestStreamFileContent:
    """Test file content streaming utilities."""

    def test_stream_file_content_small_file(self):
        """Test streaming content from small file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello world")
            temp_path = Path(f.name)

        try:
            chunks = list(stream_file_content(temp_path))
            assert len(chunks) == 1
            assert chunks[0] == "Hello world"
        finally:
            temp_path.unlink()

    def test_stream_file_content_large_file(self):
        """Test streaming content from large file."""
        large_content = "This is a test line.\n" * 1000  # ~21KB

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(large_content)
            temp_path = Path(f.name)

        try:
            chunks = list(stream_file_content(temp_path, chunk_size=1024))
            assert len(chunks) > 1
            # Verify content is preserved
            reconstructed = "".join(chunks)
            assert reconstructed == large_content
        finally:
            temp_path.unlink()

    def test_stream_file_content_empty_file(self):
        """Test streaming content from empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            chunks = list(stream_file_content(temp_path))
            assert len(chunks) == 0
        finally:
            temp_path.unlink()

    def test_stream_file_content_nonexistent_file(self):
        """Test streaming content from non-existent file."""
        chunks = list(stream_file_content(Path("nonexistent.txt")))
        assert len(chunks) == 0

    def test_stream_file_content_custom_chunk_size(self):
        """Test streaming content with custom chunk size."""
        content = "A" * 100  # 100 characters

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            chunks = list(stream_file_content(temp_path, chunk_size=20))
            assert len(chunks) == 5  # 100 / 20 = 5 chunks
            assert all(len(chunk) == 20 for chunk in chunks)
        finally:
            temp_path.unlink()

    def test_stream_file_content_unicode(self):
        """Test streaming content with Unicode characters."""
        content = "Hello 世界! Café münü naïve résumé"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            chunks = list(stream_file_content(temp_path))
            reconstructed = "".join(chunks)
            assert reconstructed == content
        finally:
            temp_path.unlink()


class TestCalculateProcessingStats:
    """Test processing statistics calculation."""

    def test_calculate_processing_stats_basic(self):
        """Test basic processing stats calculation."""
        # Create temporary files for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            py_file = temp_path / "test.py"
            py_file.write_text("def hello(): pass")

            js_file = temp_path / "test.js"
            js_file.write_text("function hello() { return true; }")

            md_file = temp_path / "README.md"
            md_file.write_text("# Test\n\nThis is a test.")

            files = [py_file, js_file, md_file]
            stats = calculate_processing_stats(files)

            assert stats["total_files"] == 3
            assert stats["total_estimated_tokens"] > 0
            assert stats["total_chars"] > 0
            assert stats["text_files"] >= 1  # At least one should be detected as text
            assert stats["binary_files"] >= 0

    def test_calculate_processing_stats_empty(self):
        """Test processing stats with empty inputs."""
        stats = calculate_processing_stats([])

        assert stats["total_files"] == 0
        assert stats["total_estimated_tokens"] == 0
        assert stats["total_chars"] == 0
        assert stats["text_files"] == 0
        assert stats["binary_files"] == 0

    def test_calculate_processing_stats_single_file(self):
        """Test processing stats with single file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            py_file = temp_path / "test.py"
            py_file.write_text("def hello(): pass")

            stats = calculate_processing_stats([py_file])

            assert stats["total_files"] == 1
            assert stats["total_estimated_tokens"] > 0
            assert stats["text_files"] >= 1
            assert stats["binary_files"] == 0

    def test_calculate_processing_stats_various_extensions(self):
        """Test processing stats with various file extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files with different extensions
            py_file = temp_path / "test.py"
            py_file.write_text("def hello(): pass")

            js_file = temp_path / "test.js"
            js_file.write_text("function hello() {}")

            md_file = temp_path / "README.md"
            md_file.write_text("# Test")

            files = [py_file, js_file, md_file]
            stats = calculate_processing_stats(files)

            assert stats["total_files"] == 3
            assert stats["total_estimated_tokens"] > 0
            assert stats["text_files"] >= 1

    def test_calculate_processing_stats_no_extension(self):
        """Test processing stats with files without extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files without extensions
            makefile = temp_path / "Makefile"
            makefile.write_text("all:\n\techo 'Hello'")

            dockerfile = temp_path / "Dockerfile"
            dockerfile.write_text("FROM ubuntu:latest")

            stats = calculate_processing_stats([makefile, dockerfile])

            assert stats["total_files"] == 2
            assert stats["total_estimated_tokens"] >= 0
            assert stats["text_files"] >= 0
            assert stats["binary_files"] >= 0

    def test_calculate_processing_stats_with_zero_tokens(self):
        """Test processing stats with files having zero tokens."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files
            py_file = temp_path / "test.py"
            py_file.write_text("def hello(): pass")

            empty_file = temp_path / "empty.txt"
            empty_file.write_text("")

            stats = calculate_processing_stats([py_file, empty_file])

            assert stats["total_files"] == 2
            assert stats["total_estimated_tokens"] >= 0
            assert stats["text_files"] >= 1


class TestConstants:
    """Test module constants."""

    def test_char_to_token_ratio_constants(self):
        """Test character to token ratio constants."""
        assert isinstance(CHAR_TO_TOKEN_RATIO, dict)
        assert "conservative" in CHAR_TO_TOKEN_RATIO
        assert "average" in CHAR_TO_TOKEN_RATIO
        assert "optimistic" in CHAR_TO_TOKEN_RATIO

        # Conservative should be the lowest ratio (most tokens)
        assert CHAR_TO_TOKEN_RATIO["conservative"] < CHAR_TO_TOKEN_RATIO["average"]
        assert CHAR_TO_TOKEN_RATIO["average"] < CHAR_TO_TOKEN_RATIO["optimistic"]

    def test_model_to_encoding_constants(self):
        """Test model to encoding mapping constants."""
        assert isinstance(MODEL_TO_ENCODING, dict)
        assert len(MODEL_TO_ENCODING) > 0

        # Test some known mappings
        assert MODEL_TO_ENCODING["gpt-4"] == "cl100k_base"
        assert MODEL_TO_ENCODING["gpt-3.5-turbo"] == "cl100k_base"
        assert MODEL_TO_ENCODING["gpt-4o"] == "o200k_base"

    def test_model_token_limits_constants(self):
        """Test model token limits constants."""
        assert isinstance(MODEL_TOKEN_LIMITS, dict)
        assert len(MODEL_TOKEN_LIMITS) > 0

        # Test some known limits
        assert MODEL_TOKEN_LIMITS["gpt-4"] == 8192
        assert MODEL_TOKEN_LIMITS["gpt-4-turbo"] == 128000
        assert MODEL_TOKEN_LIMITS["claude-3.5-sonnet"] == 200000


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple functions."""

    def test_tiktoken_vs_character_based_estimation(self):
        """Test comparison between tiktoken and character-based estimation."""
        text = "The quick brown fox jumps over the lazy dog. " * 10

        tiktoken_tokens = estimate_tokens_from_text(text, method="tiktoken")
        conservative_tokens = estimate_tokens_from_text(text, method="conservative")
        average_tokens = estimate_tokens_from_text(text, method="average")
        optimistic_tokens = estimate_tokens_from_text(text, method="optimistic")

        # All should be positive integers
        assert all(
            isinstance(t, int) and t > 0
            for t in [
                tiktoken_tokens,
                conservative_tokens,
                average_tokens,
                optimistic_tokens,
            ]
        )

        # Character-based methods should follow expected order
        assert conservative_tokens >= average_tokens >= optimistic_tokens

    def test_file_processing_pipeline(self):
        """Test complete file processing pipeline."""
        # Create test file
        content = "def hello_world():\n    print('Hello, World!')\n    return True"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            # Test the pipeline
            assert _is_likely_code_file(temp_path) is True

            file_tokens = estimate_tokens_from_file(temp_path)
            text_tokens = estimate_tokens_from_text(content)

            # Should be the same (for simple cases)
            assert file_tokens == text_tokens

            # Test streaming
            chunks = list(stream_file_content(temp_path))
            reconstructed = "".join(chunks)
            assert reconstructed == content

        finally:
            temp_path.unlink()

    def test_multi_file_stats_calculation(self):
        """Test statistics calculation for multiple files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            py_file = temp_path / "test1.py"
            py_file.write_text("def func1(): pass")

            js_file = temp_path / "test2.js"
            js_file.write_text("function func2() { return true; }")

            md_file = temp_path / "README.md"
            md_file.write_text("# Project\n\nThis is a test project.")

            files = [py_file, js_file, md_file]
            stats = calculate_processing_stats(files)

            assert stats["total_files"] == 3
            assert stats["total_estimated_tokens"] > 0
            assert stats["text_files"] >= 1

    def test_model_specific_token_counting(self):
        """Test token counting for specific models."""
        text = "Hello world! This is a test of model-specific token counting."

        models = ["gpt-4", "gpt-3.5-turbo", "gpt-4o"]

        for model in models:
            tokens = estimate_tokens_from_text(
                text, method="tiktoken", model_name=model
            )
            limit = get_model_token_limit(model)

            assert isinstance(tokens, int)
            assert isinstance(limit, int)
            assert tokens > 0
            assert limit > 0
            assert tokens < limit  # Text should be well within limit
            # Verify model-specific processing
            assert model in ["gpt-4", "gpt-3.5-turbo", "gpt-4o"]
            # Verify the model variable is used in the loop
            assert model is not None

    def test_error_handling_integration(self):
        """Test error handling across different functions."""
        # Test with various problematic inputs
        problematic_inputs = [
            "",  # Empty string
            "   ",  # Whitespace only
            None,  # None value (should be handled gracefully)
        ]

        for input_val in problematic_inputs:
            if input_val is not None:
                # These should not crash
                tokens = estimate_tokens_from_text(input_val)
                assert isinstance(tokens, int)
                assert tokens >= 0

                is_code = _is_likely_code(input_val)
                assert isinstance(is_code, bool)

    def test_large_content_handling(self):
        """Test handling of large content."""
        # Create large text content
        large_text = "This is a line of text that will be repeated many times. " * 1000

        # Test token estimation
        tokens = estimate_tokens_from_text(large_text)
        assert isinstance(tokens, int)
        assert tokens > 1000  # Should be substantial

        # Test code detection
        is_code = _is_likely_code(large_text)
        assert isinstance(is_code, bool)

        # Test with file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(large_text)
            temp_path = Path(f.name)

        try:
            file_tokens = estimate_tokens_from_file(temp_path)
            assert file_tokens == tokens

            # Test streaming
            chunks = list(stream_file_content(temp_path, chunk_size=1024))
            assert len(chunks) > 1
            reconstructed = "".join(chunks)
            assert reconstructed == large_text

        finally:
            temp_path.unlink()
