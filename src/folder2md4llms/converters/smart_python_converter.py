"""Smart Python converter that integrates with the anti-truncation engine."""

from pathlib import Path

from ..analyzers.priority_analyzer import ContentPriorityAnalyzer, PriorityLevel
from ..analyzers.progressive_condenser import ProgressiveCondenser
from ..utils.smart_budget_manager import BudgetAllocation
from ..utils.token_utils import estimate_tokens_from_text
from .base import BaseConverter


class SmartPythonConverter(BaseConverter):
    """Smart Python converter with priority-aware condensing and budget management."""

    def __init__(self, config: dict | None = None):
        """Initialize the smart Python converter.

        Args:
            config: Configuration dictionary with optional keys:
                - condense_python: Whether to condense Python code
                - python_condense_mode: Mode for condensing
                - smart_condensing: Whether to use smart condensing
        """
        super().__init__(config)
        self.condense_python = config.get("condense_python", False) if config else False
        self.smart_condensing = (
            config.get("smart_condensing", False) if config else False
        )
        self.condense_mode = (
            config.get("python_condense_mode", "signatures_with_docstrings")
            if config
            else "signatures_with_docstrings"
        )

        # Initialize smart components if enabled
        self.priority_analyzer: ContentPriorityAnalyzer | None
        self.progressive_condenser: ProgressiveCondenser | None
        if self.smart_condensing:
            self.priority_analyzer = ContentPriorityAnalyzer()
            self.progressive_condenser = ProgressiveCondenser()
        else:
            self.priority_analyzer = None
            self.progressive_condenser = None

        # Budget allocations (will be set by budget manager)
        self.budget_allocations: dict[Path, BudgetAllocation] = {}

    def can_convert(self, file_path: Path) -> bool:
        """Check if this converter can handle the file.

        Args:
            file_path: Path to the file

        Returns:
            True if this converter can handle Python files and condensing is enabled
        """
        return self.condense_python and file_path.suffix.lower() == ".py"

    def set_budget_allocation(
        self, file_path: Path, allocation: BudgetAllocation
    ) -> None:
        """Set budget allocation for a specific file.

        Args:
            file_path: Path to the file
            allocation: Budget allocation information
        """
        self.budget_allocations[file_path] = allocation

    def convert(self, file_path: Path) -> str | None:
        """Convert Python file to condensed format with smart features.

        Args:
            file_path: Path to the Python file

        Returns:
            Condensed Python code or None if conversion failed
        """
        if not self.condense_python:
            return None

        try:
            # Read file content
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                return ""

            # Use smart condensing if enabled
            if (
                self.smart_condensing
                and self.priority_analyzer
                and self.progressive_condenser
            ):
                return self._smart_convert(file_path, content)
            else:
                return self._basic_convert(file_path, content)

        except Exception as e:
            return f"# Error processing Python file {file_path}: {e}"

    def _smart_convert(self, file_path: Path, content: str) -> str:
        """Perform smart conversion with priority analysis and budget management."""
        # Analyze file priority
        file_priority = (
            self.priority_analyzer.analyze_file_priority(file_path, content)
            if self.priority_analyzer
            else PriorityLevel.MEDIUM
        )

        # Get budget allocation if available
        allocation = self.budget_allocations.get(file_path)
        available_tokens = allocation.allocated_tokens if allocation else None

        # If no budget allocation, estimate conservative limit
        if available_tokens is None:
            total_tokens = estimate_tokens_from_text(content)
            available_tokens = total_tokens  # No limit if no allocation

        # Apply progressive condensing
        if self.progressive_condenser:
            (
                condensed_content,
                condensing_info,
            ) = self.progressive_condenser.condense_with_budget(
                content=content,
                file_path=file_path,
                available_tokens=available_tokens,
                priority=file_priority,
            )
        else:
            condensed_content = content
            condensing_info = {}

        # Generate enhanced header with smart analysis info
        header = self._generate_smart_header(
            file_path, file_priority, condensing_info, allocation
        )

        return header + condensed_content

    def _basic_convert(self, file_path: Path, content: str) -> str:
        """Perform basic conversion without smart features."""
        # Fall back to existing Python analyzer
        from ..analyzers.code_analyzer import PythonCodeAnalyzer

        analyzer = PythonCodeAnalyzer(condense_mode=self.condense_mode)
        result = analyzer.analyze_code(content, str(file_path))

        if result:
            # Add basic metadata header
            header = f"# Python Code Analysis: {file_path.name}\n"
            header += f"# Condensed using mode: {self.condense_mode}\n"
            header += f"# Original file: {file_path}\n\n"

            return header + result

        return content  # Return original if analysis fails

    def _generate_smart_header(
        self,
        file_path: Path,
        priority: PriorityLevel,
        condensing_info: dict,
        allocation: BudgetAllocation | None,
    ) -> str:
        """Generate enhanced header with smart analysis information."""
        header_lines = [
            f"# Smart Python Analysis: {file_path.name}",
            f"# Priority Level: {priority.name}",
            f"# Condensing Level: {condensing_info.get('level', 'unknown')}",
            f"# Compression Ratio: {condensing_info.get('compression_ratio', 1.0):.2f}",
        ]

        if allocation:
            header_lines.extend(
                [
                    f"# Token Budget: {allocation.allocated_tokens:,}",
                    f"# Estimated Tokens: {allocation.estimated_content_tokens:,}",
                ]
            )

        header_lines.extend(
            [
                f"# Tokens Saved: {condensing_info.get('tokens_saved', 0):,}",
                f"# Final Tokens: {condensing_info.get('final_tokens', 0):,}",
                f"# Original file: {file_path}",
                "",
            ]
        )

        return "\n".join(header_lines) + "\n"

    def convert_with_priority_analysis(
        self, file_path: Path, content: str, available_tokens: int
    ) -> tuple[str, dict]:
        """Convert with explicit priority analysis and token budget.

        Args:
            file_path: Path to the file
            content: File content
            available_tokens: Available token budget

        Returns:
            Tuple of (converted_content, analysis_info)
        """
        if (
            not self.smart_condensing
            or not self.priority_analyzer
            or not self.progressive_condenser
        ):
            # Fall back to basic conversion
            basic_result = self._basic_convert(file_path, content)
            return basic_result, {"priority": "unknown", "method": "basic"}

        # Analyze file and function priorities
        file_priority = (
            self.priority_analyzer.analyze_file_priority(file_path, content)
            if self.priority_analyzer
            else PriorityLevel.MEDIUM
        )

        # Apply progressive condensing
        if self.progressive_condenser:
            (
                condensed_content,
                condensing_info,
            ) = self.progressive_condenser.condense_with_budget(
                content=content,
                file_path=file_path,
                available_tokens=available_tokens,
                priority=file_priority,
            )
        else:
            condensed_content = content
            condensing_info = {}

        # Prepare analysis info
        analysis_info = {
            "priority": file_priority.name
            if hasattr(file_priority, "name")
            else str(file_priority),
            "method": "smart",
            "condensing_info": condensing_info,
            "original_tokens": estimate_tokens_from_text(content),
            "final_tokens": estimate_tokens_from_text(condensed_content),
        }

        # Generate header
        header = self._generate_smart_header(
            file_path, file_priority, condensing_info, None
        )

        return header + condensed_content, analysis_info

    def analyze_function_priorities(self, content: str) -> dict[str, PriorityLevel]:
        """Analyze priorities of individual functions in the content.

        Args:
            content: Python source code

        Returns:
            Dictionary mapping function names to their priority levels
        """
        if not self.priority_analyzer:
            return {}

        function_priorities = {}

        try:
            import ast

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Extract function content for analysis
                    lines = content.split("\n")
                    if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                        start = max(0, node.lineno - 1)
                        end = min(len(lines), node.end_lineno or len(lines))
                        function_content = "\n".join(lines[start:end])

                        priority = self.priority_analyzer.analyze_function_priority(
                            function_content
                        )
                        function_priorities[node.name] = priority

        except SyntaxError:
            pass

        return function_priorities

    def get_supported_extensions(self) -> set:
        """Get supported file extensions.

        Returns:
            Set of supported file extensions
        """
        return {".py"}

    def get_conversion_info(self) -> dict:
        """Get information about this converter.

        Returns:
            Dictionary with converter information
        """
        info = {
            "name": "Smart Python Code Analyzer",
            "description": "Intelligent Python code analysis with priority-aware condensing",
            "supported_extensions": list(self.get_supported_extensions()),
            "condense_python": self.condense_python,
            "condense_mode": self.condense_mode,
            "smart_condensing": self.smart_condensing,
            "dependencies": ["ast (built-in)"],
        }

        if self.smart_condensing:
            info.update(
                {
                    "features": [
                        "Priority-based file analysis",
                        "Progressive condensing levels",
                        "Token budget management",
                        "Function-level priority analysis",
                        "Context-aware optimization",
                    ]
                }
            )

        return info

    def get_stats(self) -> dict:
        """Get statistics from the smart conversion process.

        Returns:
            Dictionary with conversion statistics
        """
        stats = {
            "files_processed": 0,
            "smart_conversions": 0,
            "basic_conversions": 0,
            "total_tokens_saved": 0,
        }

        if self.progressive_condenser:
            condenser_stats = self.progressive_condenser.get_condensing_stats()
            stats.update(condenser_stats)

        return stats
