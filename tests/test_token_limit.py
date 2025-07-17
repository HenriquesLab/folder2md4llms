"""Test token limit functionality."""

from pathlib import Path

import pytest

from folder2md4llms.analyzers.priority_analyzer import PriorityLevel
from folder2md4llms.engine.smart_engine import SmartAntiTruncationEngine
from folder2md4llms.utils.smart_budget_manager import BudgetStrategy
from folder2md4llms.utils.token_utils import estimate_tokens_from_text


class TestTokenLimitFunctionality:
    """Test token limit and smart engine functionality."""

    def test_smart_engine_initialization(self):
        """Test that smart engine initializes correctly with token limit."""
        engine = SmartAntiTruncationEngine(
            total_token_limit=1000, strategy=BudgetStrategy.BALANCED
        )

        assert engine.total_token_limit == 1000
        assert engine.strategy == BudgetStrategy.BALANCED
        assert engine.stats["files_processed"] == 0
        assert engine.stats["chunks_created"] == 0

    def test_smart_engine_invalid_token_limit(self):
        """Test that smart engine raises error for invalid token limit."""
        with pytest.raises(ValueError, match="Total token limit must be positive"):
            SmartAntiTruncationEngine(
                total_token_limit=0, strategy=BudgetStrategy.BALANCED
            )

    def test_token_estimation_edge_cases(self):
        """Test token estimation with edge cases."""
        # Empty text
        assert estimate_tokens_from_text("") == 0

        # Very short text
        result = estimate_tokens_from_text("a")
        assert result >= 0  # Single character might be 0 tokens due to rounding

        # Code vs text
        code_text = "def hello(): print('world')"
        natural_text = "Hello world, this is a test."

        code_tokens = estimate_tokens_from_text(code_text)
        natural_tokens = estimate_tokens_from_text(natural_text)

        assert code_tokens > 0
        assert natural_tokens > 0

    def test_budget_allocation_basic(self):
        """Test basic budget allocation."""
        engine = SmartAntiTruncationEngine(
            total_token_limit=1000, strategy=BudgetStrategy.BALANCED
        )

        # Mock file paths and priorities
        file_paths = [Path("test1.py"), Path("test2.py")]

        # Run repository analysis
        priorities, token_estimates, import_scores = engine.analyze_repository(
            file_paths, Path(".")
        )

        # Check that analysis returns expected structure
        assert isinstance(priorities, dict)
        assert isinstance(token_estimates, dict)
        assert isinstance(import_scores, dict)

    def test_file_processing_with_budget(self):
        """Test file processing with budget constraints."""
        engine = SmartAntiTruncationEngine(
            total_token_limit=100,  # Very small limit
            strategy=BudgetStrategy.BALANCED,
        )

        # Test content that exceeds budget
        large_content = "# This is a test file\n" * 50

        allocation = {"allocated_tokens": 50, "priority": PriorityLevel.MEDIUM}

        processed_content, info = engine.process_file_with_budget(
            Path("test.py"), large_content, allocation
        )

        assert processed_content != large_content  # Should be different
        assert info["method"] in ["progressive_condensing", "intelligent_truncation"]
        assert info["final_tokens"] <= 50  # Should respect budget

    def test_stats_tracking(self):
        """Test that statistics are tracked correctly."""
        engine = SmartAntiTruncationEngine(
            total_token_limit=1000, strategy=BudgetStrategy.BALANCED
        )

        initial_stats = engine.stats.copy()

        # Process a file
        content = "def test(): pass"
        allocation = {"allocated_tokens": 100, "priority": PriorityLevel.MEDIUM}

        engine.process_file_with_budget(Path("test.py"), content, allocation)

        # Check that stats were updated
        final_stats = engine.stats
        assert final_stats["files_processed"] >= initial_stats["files_processed"]

    def test_empty_content_handling(self):
        """Test handling of empty content."""
        engine = SmartAntiTruncationEngine(
            total_token_limit=1000, strategy=BudgetStrategy.BALANCED
        )

        processed_content, info = engine.process_file_with_budget(
            Path("empty.py"), "", None
        )

        assert processed_content == ""
        assert info["method"] == "unchanged"
        assert info["reason"] == "empty_content"

    def test_budget_report_generation(self):
        """Test budget report generation."""
        engine = SmartAntiTruncationEngine(
            total_token_limit=1000, strategy=BudgetStrategy.BALANCED
        )

        report = engine.get_budget_report()

        assert "engine_stats" in report
        assert "total_token_limit" in report
        assert "strategy" in report
        assert report["total_token_limit"] == 1000
        assert report["strategy"] == "balanced"

    def test_stats_format_with_smart_condensing(self):
        """Test that stats format shows condensing information when smart engine is used."""
        from folder2md4llms.formatters.markdown import MarkdownFormatter

        # Test with smart engine active
        processing_stats = {
            "file_count": 50,
            "token_count": 75000,
            "smart_engine_active": True,
            "original_tokens": 100000,
            "condensed_tokens": 75000,
        }

        formatter = MarkdownFormatter(smart_engine_active=True)
        preamble = formatter._generate_preamble(Path("/test/repo"), processing_stats)

        # Should show condensing format
        assert "75,000/100,000 tokens (25.0% condensed)" in preamble
        assert "50 files" in preamble

    def test_stats_format_without_smart_condensing(self):
        """Test that stats format shows regular information when smart engine is not used."""
        from folder2md4llms.formatters.markdown import MarkdownFormatter

        # Test without smart engine
        processing_stats = {
            "file_count": 50,
            "token_count": 75000,
        }

        formatter = MarkdownFormatter(smart_engine_active=False)
        preamble = formatter._generate_preamble(Path("/test/repo"), processing_stats)

        # Should show regular format
        assert "75,000 tokens" in preamble
        assert "50 files" in preamble
        assert "condensed" not in preamble

    def test_stats_format_no_condensing_needed(self):
        """Test stats format when no condensing was needed."""
        from folder2md4llms.formatters.markdown import MarkdownFormatter

        # Test with smart engine active but no condensing needed
        processing_stats = {
            "file_count": 50,
            "token_count": 75000,
            "smart_engine_active": True,
            "original_tokens": 75000,
            "condensed_tokens": 75000,
        }

        formatter = MarkdownFormatter(smart_engine_active=True)
        preamble = formatter._generate_preamble(Path("/test/repo"), processing_stats)

        # Should show 0% condensed
        assert "75,000/75,000 tokens (0.0% condensed)" in preamble
