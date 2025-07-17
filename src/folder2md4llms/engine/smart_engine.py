"""Smart anti-truncation engine that orchestrates intelligent content processing."""

from pathlib import Path

from ..analyzers.priority_analyzer import ContentPriorityAnalyzer, PriorityLevel
from ..analyzers.progressive_condenser import ProgressiveCondenser
from ..utils.smart_budget_manager import BudgetStrategy, SmartTokenBudgetManager
from ..utils.smart_chunker import SmartChunker
from ..utils.token_utils import estimate_tokens_from_text


class SmartAntiTruncationEngine:
    """Orchestrates intelligent content processing to minimize truncation."""

    def __init__(
        self,
        total_token_limit: int,
        strategy: BudgetStrategy = BudgetStrategy.BALANCED,
        enable_chunking: bool = True,
        enable_priority_analysis: bool = True,
        enable_progressive_condensing: bool = True,
    ):
        """Initialize the smart engine.

        Args:
            total_token_limit: Total token budget for output
            strategy: Budget allocation strategy
            enable_chunking: Whether to enable smart chunking
            enable_priority_analysis: Whether to analyze content priorities
            enable_progressive_condensing: Whether to use progressive condensing
        """
        self.total_token_limit = total_token_limit
        self.strategy = strategy
        self.enable_chunking = enable_chunking
        self.enable_priority_analysis = enable_priority_analysis
        self.enable_progressive_condensing = enable_progressive_condensing

        # Initialize components
        self.budget_manager = (
            SmartTokenBudgetManager(
                total_token_limit=total_token_limit, strategy=strategy
            )
            if total_token_limit
            else None
        )

        self.priority_analyzer = (
            ContentPriorityAnalyzer() if enable_priority_analysis else None
        )

        self.progressive_condenser = (
            ProgressiveCondenser() if enable_progressive_condensing else None
        )

        self.smart_chunker = SmartChunker() if enable_chunking else None

        # Track processing statistics
        self.stats = {
            "files_processed": 0,
            "total_tokens_saved": 0,
            "budget_allocations_made": 0,
            "chunks_created": 0,
            "priority_analyses_performed": 0,
            "progressive_condensing_applied": 0,
        }

    def analyze_repository(
        self, file_paths: list[Path], repo_path: Path
    ) -> tuple[dict[Path, PriorityLevel], dict[Path, int], dict[Path, float]]:
        """Analyze entire repository to determine priorities and token estimates.

        Args:
            file_paths: List of files to analyze
            repo_path: Repository root path

        Returns:
            Tuple of (file_priorities, token_estimates, import_scores)
        """
        file_priorities = {}
        token_estimates = {}
        import_scores = {}

        # Analyze file priorities and estimate tokens
        for file_path in file_paths:
            try:
                # Read file content for analysis
                content = ""
                if file_path.is_file() and self._is_text_file(file_path):
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            content = f.read()
                    except (OSError, UnicodeDecodeError):
                        content = ""

                # Analyze priority
                if self.priority_analyzer:
                    priority = self.priority_analyzer.analyze_file_priority(
                        file_path, content
                    )
                    file_priorities[file_path] = priority
                    self.stats["priority_analyses_performed"] += 1
                else:
                    file_priorities[file_path] = PriorityLevel.MEDIUM

                # Estimate tokens
                if content:
                    tokens = estimate_tokens_from_text(content)
                    token_estimates[file_path] = tokens
                else:
                    token_estimates[file_path] = 0

            except Exception:
                # Handle errors gracefully
                file_priorities[file_path] = PriorityLevel.LOW
                token_estimates[file_path] = 0

        # Analyze import graph for Python files
        if self.priority_analyzer:
            try:
                import_scores = self.priority_analyzer.analyze_import_graph(repo_path)
            except Exception:
                import_scores = {}

        return file_priorities, token_estimates, import_scores

    def allocate_budgets(
        self,
        file_priorities: dict[Path, PriorityLevel],
        token_estimates: dict[Path, int],
        import_scores: dict[Path, float] | None = None,
    ) -> dict:
        """Allocate token budgets across files based on priorities.

        Args:
            file_priorities: File priority mappings
            token_estimates: Token estimate mappings
            import_scores: Optional import importance scores

        Returns:
            Budget allocation results
        """
        if not self.budget_manager:
            return {}

        allocations = self.budget_manager.allocate_budget(
            file_priorities=file_priorities,
            file_token_estimates=token_estimates,
            import_scores=import_scores,
        )

        self.stats["budget_allocations_made"] = len(allocations)

        return allocations

    def process_file_with_budget(
        self, file_path: Path, content: str, allocation: dict | None = None
    ) -> tuple[str, dict]:
        """Process a single file with intelligent budget management.

        Args:
            file_path: Path to the file
            content: File content
            allocation: Budget allocation for this file

        Returns:
            Tuple of (processed_content, processing_info)
        """
        if not content.strip():
            return content, {"method": "unchanged", "reason": "empty_content"}

        # Determine available tokens
        if allocation and "allocated_tokens" in allocation:
            available_tokens = allocation["allocated_tokens"]
            priority = allocation.get("priority", PriorityLevel.MEDIUM)
        else:
            available_tokens = estimate_tokens_from_text(content)
            priority = PriorityLevel.MEDIUM

        processing_info = {
            "original_tokens": estimate_tokens_from_text(content),
            "available_tokens": available_tokens,
            "priority": priority.name if hasattr(priority, "name") else str(priority),
            "method": "smart_engine",
        }

        # Check if condensing is needed
        original_tokens = processing_info["original_tokens"]

        if original_tokens <= available_tokens:
            # No condensing needed
            processing_info.update(
                {
                    "method": "unchanged",
                    "reason": "fits_in_budget",
                    "final_tokens": original_tokens,
                }
            )
            return content, processing_info

        # Apply progressive condensing if enabled
        if self.enable_progressive_condensing and self.progressive_condenser:
            (
                condensed_content,
                condensing_info,
            ) = self.progressive_condenser.condense_with_budget(
                content=content,
                file_path=file_path,
                available_tokens=available_tokens,
                priority=priority,
            )

            processing_info.update(
                {
                    "method": "progressive_condensing",
                    "condensing_info": condensing_info,
                    "final_tokens": condensing_info.get(
                        "final_tokens", original_tokens
                    ),
                    "tokens_saved": condensing_info.get("tokens_saved", 0),
                }
            )

            self.stats["progressive_condensing_applied"] += 1
            self.stats["total_tokens_saved"] += condensing_info.get("tokens_saved", 0)

            # Check if chunking is still needed
            final_tokens = processing_info["final_tokens"]
            if final_tokens <= available_tokens or not self.enable_chunking:
                return condensed_content, processing_info
            else:
                # Apply smart chunking to condensed content
                return self._apply_smart_chunking(
                    condensed_content, file_path, available_tokens, processing_info
                )

        # Fall back to chunking if no condensing available
        elif self.enable_chunking and self.smart_chunker:
            return self._apply_smart_chunking(
                content, file_path, available_tokens, processing_info
            )

        # Last resort: truncate intelligently
        else:
            return self._intelligent_truncate(
                content, available_tokens, processing_info
            )

    def _apply_smart_chunking(
        self,
        content: str,
        file_path: Path,
        available_tokens: int,
        processing_info: dict,
    ) -> tuple[str, dict]:
        """Apply smart chunking to content."""
        chunks = self.smart_chunker.chunk_with_context(
            content=content,
            file_path=file_path,
            max_tokens=available_tokens,
            priority=PriorityLevel.MEDIUM,  # Could be enhanced with actual priority
        )

        if chunks:
            # For now, return the first chunk with continuation info
            first_chunk = chunks[0]
            chunked_content = first_chunk.content

            if len(chunks) > 1:
                chunked_content += (
                    f"\n\n# [Continues in {len(chunks) - 1} more chunks...]"
                )

            processing_info.update(
                {
                    "method": "smart_chunking",
                    "total_chunks": len(chunks),
                    "chunk_info": f"Showing chunk 1 of {len(chunks)}",
                    "final_tokens": first_chunk.estimated_tokens
                    or estimate_tokens_from_text(chunked_content),
                }
            )

            self.stats["chunks_created"] += len(chunks)

            return chunked_content, processing_info

        return content, processing_info

    def _intelligent_truncate(
        self, content: str, available_tokens: int, processing_info: dict
    ) -> tuple[str, dict]:
        """Intelligently truncate content as a last resort."""
        lines = content.split("\n")

        # Keep important lines (imports, class/function definitions)
        important_lines = []
        regular_lines = []

        for line in lines:
            stripped = line.strip()
            if (
                stripped.startswith(
                    ("import ", "from ", "class ", "def ", "async def ")
                )
                or stripped.startswith("#")
                and any(
                    keyword in stripped.lower()
                    for keyword in ["todo", "fixme", "note", "important"]
                )
            ):
                important_lines.append(line)
            else:
                regular_lines.append(line)

        # Build truncated content prioritizing important lines
        truncated_lines = important_lines[:]
        current_tokens = estimate_tokens_from_text("\n".join(truncated_lines))

        # Add regular lines until we hit the limit
        for line in regular_lines:
            line_tokens = estimate_tokens_from_text(line)
            if current_tokens + line_tokens <= available_tokens * 0.9:  # Leave buffer
                truncated_lines.append(line)
                current_tokens += line_tokens
            else:
                break

        truncated_content = "\n".join(truncated_lines)
        if len(truncated_lines) < len(lines):
            truncated_content += f"\n\n# [Content truncated: {len(lines) - len(truncated_lines)} lines omitted]"

        processing_info.update(
            {
                "method": "intelligent_truncation",
                "lines_kept": len(truncated_lines),
                "lines_omitted": len(lines) - len(truncated_lines),
                "final_tokens": estimate_tokens_from_text(truncated_content),
            }
        )

        return truncated_content, processing_info

    def get_budget_report(self) -> dict:
        """Get comprehensive budget and processing report.

        Returns:
            Dictionary with detailed statistics
        """
        report = {
            "engine_stats": self.stats.copy(),
            "total_token_limit": self.total_token_limit,
            "strategy": self.strategy.value if self.strategy else "none",
        }

        if self.budget_manager:
            report["budget_report"] = self.budget_manager.get_budget_report()

        if self.progressive_condenser:
            report[
                "condensing_stats"
            ] = self.progressive_condenser.get_condensing_stats()

        if self.smart_chunker:
            report["chunking_stats"] = self.smart_chunker.get_chunking_stats()

        return report

    def suggest_optimizations(self) -> list[str]:
        """Suggest optimizations based on processing results.

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        if self.budget_manager:
            adjustments = self.budget_manager.suggest_adjustments()
            for adjustment in adjustments:
                suggestions.append(
                    f"Consider {adjustment.suggested_level} condensing for {adjustment.file_path.name} "
                    f"({adjustment.reason})"
                )

        # Add general suggestions based on stats
        if self.stats["chunks_created"] > self.stats["files_processed"] * 2:
            suggestions.append(
                "Many files were chunked - consider increasing token limit or more aggressive condensing"
            )

        if self.stats["total_tokens_saved"] < self.stats["files_processed"] * 100:
            suggestions.append(
                "Low token savings - consider enabling more aggressive condensing modes"
            )

        return suggestions

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if a file is likely a text file."""
        try:
            # Simple heuristic: try to read a small portion
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                return b"\0" not in chunk
        except (OSError, PermissionError):
            return False

    def reset_stats(self) -> None:
        """Reset all processing statistics."""
        self.stats = {
            "files_processed": 0,
            "total_tokens_saved": 0,
            "budget_allocations_made": 0,
            "chunks_created": 0,
            "priority_analyses_performed": 0,
            "progressive_condensing_applied": 0,
        }

        if self.budget_manager:
            self.budget_manager = SmartTokenBudgetManager(
                total_token_limit=self.total_token_limit, strategy=self.strategy
            )

        if self.progressive_condenser:
            self.progressive_condenser = ProgressiveCondenser()

        if self.smart_chunker:
            self.smart_chunker = SmartChunker()
