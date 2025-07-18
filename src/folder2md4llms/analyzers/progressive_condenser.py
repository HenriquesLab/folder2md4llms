"""Progressive condenser for adaptive code condensing based on available token budget."""

import ast
import re
from collections import defaultdict
from pathlib import Path

from ..utils.token_utils import estimate_tokens_from_text
from .priority_analyzer import PriorityLevel


class CondensingLevel:
    """Defines different levels of code condensing."""

    NONE = "none"  # Full content preservation
    LIGHT = "light"  # Remove comments, empty lines
    MODERATE = "moderate"  # Signatures + docstrings
    HEAVY = "heavy"  # Signatures only
    MAXIMUM = "maximum"  # Minimal structure only


class PythonCodeAnalyzer:
    """Enhanced Python analyzer with better structure understanding."""

    def extract_class_hierarchy(self, tree: ast.AST) -> dict:
        """Extract class inheritance relationships."""
        hierarchy = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [self._get_name(base) for base in node.bases]
                hierarchy[node.name] = {
                    "bases": bases,
                    "methods": [
                        n.name for n in node.body if isinstance(n, ast.FunctionDef)
                    ],
                    "has_init": any(
                        n.name == "__init__"
                        for n in node.body
                        if isinstance(n, ast.FunctionDef)
                    ),
                    "decorators": [self._get_name(d) for d in node.decorator_list],
                }

        return hierarchy

    def identify_design_patterns(self, tree: ast.AST) -> list[str]:
        """Identify common design patterns to preserve important structure."""
        patterns = []

        # Singleton pattern
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                if "__new__" in methods or any(
                    "_instance" in str(n) for n in ast.walk(node)
                ):
                    patterns.append(f"Singleton: {node.name}")

        return patterns

    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return str(node)


class ProgressiveCondenser:
    """Adaptively condenses code based on available token budget and content priority."""

    def __init__(self):
        """Initialize the progressive condenser."""
        self.stats = {
            "files_processed": 0,
            "tokens_saved": 0,
            "condensing_levels_used": {},
        }

        # Enhanced pattern detection for better condensing
        self.python_analyzer = PythonCodeAnalyzer()

    def condense_with_budget(
        self,
        content: str,
        file_path: Path,
        available_tokens: int,
        priority: PriorityLevel,
        estimated_tokens: int | None = None,
    ) -> tuple[str, dict]:
        """Condense content based on available token budget and priority.

        Args:
            content: Original content to condense
            file_path: Path to the file (for language detection)
            available_tokens: Number of tokens available for this content
            priority: Priority level of the content
            estimated_tokens: Pre-calculated token estimate (optional)

        Returns:
            Tuple of (condensed_content, condensing_info)
        """
        if not content.strip():
            return content, {"level": CondensingLevel.NONE, "tokens_saved": 0}

        # Estimate tokens if not provided
        if estimated_tokens is None:
            estimated_tokens = estimate_tokens_from_text(content)

        # Handle empty content
        if estimated_tokens <= 0:
            return content, {"level": CondensingLevel.NONE, "tokens_saved": 0}

        # Determine target condensing level
        target_level = self._determine_condensing_level(
            estimated_tokens, available_tokens, priority
        )

        # Apply condensing based on file type and level
        condensed_content = self._apply_condensing(
            content, file_path, target_level, priority
        )

        # Calculate actual tokens saved
        final_tokens = estimate_tokens_from_text(condensed_content)
        tokens_saved = estimated_tokens - final_tokens

        # Update stats
        self.stats["files_processed"] += 1  # type: ignore[operator]
        self.stats["tokens_saved"] += tokens_saved  # type: ignore[operator]
        levels_used = self.stats["condensing_levels_used"]
        if isinstance(levels_used, dict):
            level_count = levels_used.get(target_level, 0)
            levels_used[target_level] = level_count + 1

        condensing_info = {
            "level": target_level,
            "original_tokens": estimated_tokens,
            "final_tokens": final_tokens,
            "tokens_saved": tokens_saved,
            "compression_ratio": final_tokens / estimated_tokens
            if estimated_tokens > 0
            else 1.0,
            "priority": priority.name,
        }

        return condensed_content, condensing_info

    def condense_function_selectively(
        self,
        function_content: str,
        function_priority: PriorityLevel,
        available_tokens: int,
        language: str = "python",
    ) -> str:
        """Selectively condense a function based on its priority and available budget.

        Args:
            function_content: The function's source code
            function_priority: Priority level of the function
            available_tokens: Available token budget for this function
            language: Programming language of the function

        Returns:
            Condensed function content
        """
        estimated_tokens = estimate_tokens_from_text(function_content)

        if estimated_tokens <= available_tokens:
            return function_content  # No condensing needed

        if function_priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]:
            # For important functions, try to preserve structure
            return self._condense_function_preserve_structure(
                function_content, language
            )
        else:
            # For less important functions, aggressive condensing
            return self._condense_function_minimal(function_content, language)

    def adjust_condensing_level(
        self,
        current_content: str,
        current_level: str,
        token_budget_used: int,
        total_budget: int,
    ) -> str:
        """Dynamically adjust condensing level based on budget usage.

        Args:
            current_content: Currently condensed content
            current_level: Current condensing level
            token_budget_used: Tokens used so far
            total_budget: Total token budget

        Returns:
            Suggested new condensing level
        """
        budget_usage_ratio = token_budget_used / total_budget if total_budget > 0 else 0

        # If we're using too much budget, increase condensing
        if budget_usage_ratio > 0.8:
            return self._increase_condensing_level(current_level)
        # If we have plenty of budget left, decrease condensing
        elif budget_usage_ratio < 0.5:
            return self._decrease_condensing_level(current_level)
        else:
            return current_level

    def get_condensing_stats(self) -> dict:
        """Get statistics about condensing operations.

        Returns:
            Dictionary with condensing statistics
        """
        return self.stats.copy()

    def generate_smart_statistics(self, processing_results: dict) -> dict:
        """Generate intelligent statistics about the processing."""
        stats = {
            "condensing_effectiveness": {
                "files_condensed": 0,
                "average_compression": 0.0,
                "tokens_saved": 0,
            },
            "priority_distribution": defaultdict(int),
            "framework_detected": None,
            "patterns_found": [],
            "quality_metrics": {
                "preserved_api_completeness": 0.0,
                "documentation_coverage": 0.0,
            },
        }

        # Calculate meaningful metrics
        total_compression = 0.0
        condensed_files = 0

        for file_result in processing_results.get("files", []):
            if file_result.get("condensed"):
                condensed_files += 1
                compression_ratio = file_result.get("compression_ratio", 1.0)
                total_compression += compression_ratio
                effectiveness = stats["condensing_effectiveness"]
                if isinstance(effectiveness, dict):
                    effectiveness["tokens_saved"] += file_result.get("tokens_saved", 0)  # type: ignore[operator]

            priority = file_result.get("priority", "MEDIUM")
            priority_dist = stats["priority_distribution"]
            if isinstance(priority_dist, dict):
                priority_dist[priority] += 1  # type: ignore[operator]

        if condensed_files > 0:
            effectiveness = stats["condensing_effectiveness"]
            if isinstance(effectiveness, dict):
                effectiveness["files_condensed"] = condensed_files
                effectiveness["average_compression"] = (
                    total_compression / condensed_files
                )

        return stats

    def detect_repetitive_patterns(
        self, content: str, file_extension: str
    ) -> list[tuple[str, int]]:
        """Detect repetitive code patterns that can be condensed."""
        patterns = []

        if file_extension == ".py":
            try:
                tree = ast.parse(content)
                # Extract function names from AST
                function_names = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        function_names.append(node.name)

                # Count similar patterns
                pattern_counts: dict[str, int] = defaultdict(int)
                for func_name in function_names:
                    # Normalize to detect patterns like get_X, set_X
                    normalized = re.sub(
                        r"^(get|set|create|delete|update)_\w+$", r"\1_ACTION", func_name
                    )
                    if normalized != func_name:  # Only count if pattern was found
                        pattern_counts[normalized] += 1

                # Report patterns that occur more than twice
                patterns = [(p, c) for p, c in pattern_counts.items() if c > 2]
            except SyntaxError:
                pass

        return patterns

    def create_pattern_summary(self, patterns: list[tuple[str, int]]) -> str:
        """Create a concise summary of repetitive patterns."""
        if not patterns:
            return ""

        summary = ["# Pattern Summary:"]
        for pattern, count in patterns:
            summary.append(f"# {pattern} pattern repeated {count} times")

        return "\n".join(summary)

    def _determine_condensing_level(
        self, estimated_tokens: int, available_tokens: int, priority: PriorityLevel
    ) -> str:
        """Determine the appropriate condensing level."""
        if available_tokens >= estimated_tokens:
            return CondensingLevel.NONE

        # Prevent division by zero
        if available_tokens <= 0:
            return CondensingLevel.MAXIMUM

        compression_needed = estimated_tokens / available_tokens

        # Adjust thresholds based on priority
        if priority == PriorityLevel.CRITICAL:
            # Be more conservative with critical content
            if compression_needed <= 1.3:
                return CondensingLevel.LIGHT
            elif compression_needed <= 2.0:
                return CondensingLevel.MODERATE
            elif compression_needed <= 3.0:
                return CondensingLevel.HEAVY
            else:
                return CondensingLevel.MAXIMUM
        elif priority == PriorityLevel.HIGH:
            if compression_needed <= 1.5:
                return CondensingLevel.LIGHT
            elif compression_needed <= 2.5:
                return CondensingLevel.MODERATE
            elif compression_needed <= 4.0:
                return CondensingLevel.HEAVY
            else:
                return CondensingLevel.MAXIMUM
        else:
            # Be more aggressive with lower priority content
            if compression_needed <= 2.0:
                return CondensingLevel.MODERATE
            elif compression_needed <= 3.0:
                return CondensingLevel.HEAVY
            else:
                return CondensingLevel.MAXIMUM

    def _apply_condensing(
        self, content: str, file_path: Path, level: str, priority: PriorityLevel
    ) -> str:
        """Apply the specified condensing level to content."""
        if level == CondensingLevel.NONE:
            return content

        # Apply semantic-aware condensing that preserves logical units
        return self._apply_semantic_condensing(content, level, file_path, priority)

    def _apply_semantic_condensing(
        self, content: str, level: str, file_path: Path, priority: PriorityLevel
    ) -> str:
        """Apply semantic-aware condensing that preserves logical units."""
        suffix = file_path.suffix.lower()

        if level == CondensingLevel.LIGHT:
            # Remove only truly redundant content
            content = self._remove_obvious_comments(content)
            content = self._normalize_whitespace(content)

        elif level == CondensingLevel.MODERATE:
            # Preserve structure but condense implementation
            if suffix == ".py":
                content = self._preserve_api_signatures(content)
            elif suffix in [".js", ".ts", ".jsx", ".tsx"]:
                content = self._condense_javascript_content(content, level, priority)
            elif suffix == ".java":
                content = self._condense_java_content(content, level, priority)
            else:
                content = self._condense_generic_content(content, level)

        elif level == CondensingLevel.HEAVY:
            # Keep only public interfaces
            content = self._extract_public_api(content, suffix)

        elif level == CondensingLevel.MAXIMUM:
            # Maximum condensing with pattern detection
            patterns = self.detect_repetitive_patterns(content, suffix)
            if patterns:
                content = self.create_pattern_summary(patterns)
            else:
                content = self._maximum_condense_content(content, suffix)

        return content

    def _remove_obvious_comments(self, content: str) -> str:
        """Remove obvious comments while preserving important ones."""
        lines = content.split("\n")
        result = []

        for line in lines:
            stripped = line.strip()
            # Keep docstrings and important comments
            if stripped.startswith("#") and not any(
                keyword in stripped.lower()
                for keyword in ["todo", "fixme", "hack", "note", "important", "warning"]
            ):
                # Skip obvious comments
                continue
            result.append(line)

        return "\n".join(result)

    def _normalize_whitespace(self, content: str) -> str:
        """Normalize excessive whitespace."""
        # Remove multiple consecutive empty lines
        content = re.sub(r"\n\s*\n\s*\n+", "\n\n", content)
        # Remove trailing whitespace
        lines = [line.rstrip() for line in content.split("\n")]
        return "\n".join(lines)

    def _preserve_api_signatures(self, content: str) -> str:
        """Preserve public API signatures while condensing implementation."""
        try:
            tree = ast.parse(content)
            preserved = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith("_"):  # Public method
                        # Preserve signature and docstring
                        sig_lines = self._extract_signature_and_docs(content, node)
                        preserved.extend(sig_lines)

            return "\n".join(preserved)
        except SyntaxError:
            return content

    def _extract_signature_and_docs(
        self, content: str, node: ast.FunctionDef
    ) -> list[str]:
        """Extract function signature and docstring."""
        lines = content.split("\n")
        result = []

        if hasattr(node, "lineno"):
            start_line = node.lineno - 1
            # Add function signature
            i = start_line
            while i < len(lines) and ":" not in lines[i]:
                result.append(lines[i])
                i += 1
            if i < len(lines):
                result.append(lines[i])  # Line with colon

            # Add docstring if present
            docstring = ast.get_docstring(node)
            if docstring:
                result.append('    """')
                result.append(f"    {docstring}")
                result.append('    """')

            result.append("")  # Empty line after function

        return result

    def _extract_public_api(self, content: str, file_type: str) -> str:
        """Extract only public API interfaces."""
        if file_type == ".py":
            return self._extract_python_public_api(content)
        elif file_type in [".js", ".ts", ".jsx", ".tsx"]:
            return self._extract_js_public_api(content)
        elif file_type == ".java":
            return self._extract_java_public_api(content)
        else:
            return self._condense_generic_content(content, CondensingLevel.HEAVY)

    def _extract_python_public_api(self, content: str) -> str:
        """Extract Python public API."""
        try:
            tree = ast.parse(content)
            result = []

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    result.append(f"class {node.name}:")
                    # Add public methods
                    for item in node.body:
                        if isinstance(
                            item, ast.FunctionDef
                        ) and not item.name.startswith("_"):
                            args = [arg.arg for arg in item.args.args]
                            result.append(
                                f"    def {item.name}({', '.join(args)}): ..."
                            )
                elif isinstance(node, ast.FunctionDef) and not node.name.startswith(
                    "_"
                ):
                    args = [arg.arg for arg in node.args.args]
                    result.append(f"def {node.name}({', '.join(args)}): ...")

            return "\n".join(result)
        except SyntaxError:
            return content

    def _extract_js_public_api(self, content: str) -> str:
        """Extract JavaScript/TypeScript public API."""
        # Extract exports and public functions
        exports = re.findall(
            r"export\s+(?:default\s+)?(?:function|class|const|let|var)\s+\w+", content
        )
        functions = re.findall(
            r"(?:export\s+)?(?:async\s+)?function\s+\w+\([^)]*\)", content
        )
        classes = re.findall(r"(?:export\s+)?class\s+\w+(?:\s+extends\s+\w+)?", content)

        result = []
        if exports:
            result.extend(exports[:10])
        if functions:
            result.extend(functions[:10])
        if classes:
            result.extend(classes)

        return "\n".join(result) if result else "// No public API found"

    def _extract_java_public_api(self, content: str) -> str:
        """Extract Java public API."""
        # Extract public class and method signatures
        public_classes = re.findall(
            r"public\s+class\s+\w+(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?",
            content,
        )
        public_methods = re.findall(
            r"public\s+(?:static\s+)?[\w<>\[\]]+\s+\w+\([^)]*\)", content
        )

        result = []
        if public_classes:
            result.extend(public_classes)
        if public_methods:
            result.extend(public_methods[:15])

        return "\n".join(result) if result else "// No public API found"

    def _maximum_condense_content(self, content: str, file_type: str) -> str:
        """Maximum condensing for any file type."""
        if file_type == ".py":
            try:
                tree = ast.parse(content)
                return self._maximum_condense_python(content, tree)
            except SyntaxError:
                return self._condense_generic_content(content, CondensingLevel.MAXIMUM)
        elif file_type in [".js", ".ts", ".jsx", ".tsx"]:
            return self._condense_javascript_content(
                content, CondensingLevel.MAXIMUM, PriorityLevel.LOW
            )
        elif file_type == ".java":
            return self._condense_java_content(
                content, CondensingLevel.MAXIMUM, PriorityLevel.LOW
            )
        else:
            return self._condense_generic_content(content, CondensingLevel.MAXIMUM)

    def _condense_python_content(
        self, content: str, level: str, priority: PriorityLevel
    ) -> str:
        """Condense Python content based on the specified level."""
        try:
            tree = ast.parse(content)

            # Use enhanced analysis for better condensing decisions
            # hierarchy = self.python_analyzer.extract_class_hierarchy(tree)
            # patterns = self.python_analyzer.identify_design_patterns(tree)

            if level == CondensingLevel.LIGHT:
                return self._light_condense_python(content, tree)
            elif level == CondensingLevel.MODERATE:
                return self._moderate_condense_python(content, tree, priority)
            elif level == CondensingLevel.HEAVY:
                return self._heavy_condense_python(content, tree)
            elif level == CondensingLevel.MAXIMUM:
                return self._maximum_condense_python(content, tree)

        except SyntaxError:
            # If parsing fails, fall back to generic condensing
            return self._condense_generic_content(content, level)

        return content

    def _light_condense_python(self, content: str, tree: ast.AST) -> str:
        """Light condensing: remove comments and excessive whitespace."""
        lines = content.split("\n")
        condensed_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            # Skip standalone comments but keep inline comments
            if stripped.startswith("#") and not any(
                stripped.startswith(f"#{i}") for i in range(10)
            ):
                continue
            # Skip empty lines between functions/classes
            if (
                not stripped
                and len(condensed_lines) > 0
                and not condensed_lines[-1].strip()
            ):
                continue
            condensed_lines.append(line)

        return "\n".join(condensed_lines)

    def _moderate_condense_python(
        self, content: str, tree: ast.AST, priority: PriorityLevel
    ) -> str:
        """Moderate condensing: preserve signatures and docstrings."""
        result = []
        lines = content.split("\n")

        # Get module docstring
        module_docstring = None
        if hasattr(tree, "body") and isinstance(tree, ast.Module):
            module_docstring = ast.get_docstring(tree)
        if module_docstring and priority in [
            PriorityLevel.CRITICAL,
            PriorityLevel.HIGH,
        ]:
            result.append(f'"""{module_docstring}"""')
            result.append("")

        # Process imports (keep first 10, summarize rest)
        imports = []
        if hasattr(tree, "body"):
            for node in tree.body:
                if isinstance(node, ast.Import | ast.ImportFrom):
                    imports.append(self._get_source_segment(lines, node))

        if imports:
            result.extend(imports[:10])
            if len(imports) > 10:
                result.append(f"# ... and {len(imports) - 10} more imports")
            result.append("")

        # Process classes and functions
        if hasattr(tree, "body"):
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    result.extend(self._condense_python_class(node, lines, priority))
                    result.append("")
                elif isinstance(node, ast.FunctionDef):
                    result.extend(self._condense_python_function(node, lines, priority))
                    result.append("")

        return "\n".join(result)

    def _heavy_condense_python(self, content: str, tree: ast.AST) -> str:
        """Heavy condensing: signatures only."""
        result = []
        lines = content.split("\n")

        # Essential imports only
        essential_imports = []
        if hasattr(tree, "body"):
            for node in tree.body:
                if isinstance(node, ast.Import | ast.ImportFrom):
                    import_line = self._get_source_segment(lines, node)
                    if any(
                        keyword in import_line.lower()
                        for keyword in ["from __future__", "import os", "import sys"]
                    ):
                        essential_imports.append(import_line)

        if essential_imports:
            result.extend(essential_imports[:5])
            result.append("")

        # Class and function signatures only
        if hasattr(tree, "body"):
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    result.append(self._get_class_signature(node, lines))
                    # Include only critical methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name in [
                            "__init__",
                            "__call__",
                            "main",
                        ]:
                            result.append(
                                "    " + self._get_function_signature(item, lines)
                            )
                    result.append("")
                elif isinstance(node, ast.FunctionDef):
                    result.append(self._get_function_signature(node, lines))

        return "\n".join(result)

    def _maximum_condense_python(self, content: str, tree: ast.AST) -> str:
        """Maximum condensing: minimal structure overview."""
        result = []

        classes = []
        functions = []

        if hasattr(tree, "body"):
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    methods = [
                        item.name
                        for item in node.body
                        if isinstance(item, ast.FunctionDef)
                    ]
                    classes.append(
                        f"class {node.name}: # Methods: {', '.join(methods[:5])}"
                    )
                elif isinstance(node, ast.FunctionDef):
                    functions.append(f"def {node.name}(...)")

        if classes:
            result.append("# Classes:")
            result.extend(classes)
            result.append("")

        if functions:
            result.append("# Functions:")
            result.extend(functions[:10])
            if len(functions) > 10:
                result.append(f"# ... and {len(functions) - 10} more functions")

        return "\n".join(result)

    def _condense_javascript_content(
        self, content: str, level: str, priority: PriorityLevel
    ) -> str:
        """Condense JavaScript/TypeScript content."""
        if level == CondensingLevel.LIGHT:
            # Remove comments and extra whitespace
            content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
            content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
            content = re.sub(r"\n\s*\n", "\n", content)
            return content

        elif level in [CondensingLevel.MODERATE, CondensingLevel.HEAVY]:
            # Extract function signatures and exports
            functions = re.findall(
                r"(?:export\s+)?(?:async\s+)?function\s+\w+\([^)]*\)", content
            )
            classes = re.findall(
                r"(?:export\s+)?class\s+\w+(?:\s+extends\s+\w+)?", content
            )
            exports = re.findall(
                r"export\s+(?:default\s+)?(?:const|let|var|function|class)\s+\w+",
                content,
            )

            result = []
            if exports:
                result.extend(exports[:10])
            if functions:
                result.extend(functions[:10])
            if classes:
                result.extend(classes)

            return "\n".join(result)

        else:  # MAXIMUM
            # Just show exports and main structures
            exports = re.findall(r"export\s+.*", content)
            return (
                "\n".join(exports[:5]) if exports else "// JavaScript/TypeScript module"
            )

    def _condense_java_content(
        self, content: str, level: str, priority: PriorityLevel
    ) -> str:
        """Condense Java content."""
        if level == CondensingLevel.LIGHT:
            # Remove comments
            content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
            content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
            return content

        elif level in [CondensingLevel.MODERATE, CondensingLevel.HEAVY]:
            # Extract class signatures and public methods
            package = re.search(r"package\s+[\w.]+;", content)
            imports = re.findall(r"import\s+[\w.]+;", content)
            classes = re.findall(
                r"(?:public\s+)?class\s+\w+(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?",
                content,
            )
            methods = re.findall(
                r"(?:public|private|protected)?\s+(?:static\s+)?[\w<>\[\]]+\s+\w+\([^)]*\)",
                content,
            )

            result = []
            if package:
                result.append(package.group())
            if imports:
                result.extend(imports[:5])
            if classes:
                result.extend(classes)
            if methods and level == CondensingLevel.MODERATE:
                result.extend(methods[:10])

            return "\n".join(result)

        else:  # MAXIMUM
            # Just package and class declarations
            package = re.search(r"package\s+[\w.]+;", content)
            classes = re.findall(r"class\s+\w+", content)
            result = []
            if package:
                result.append(package.group())
            if classes:
                result.extend([f"// {cls}" for cls in classes])
            return "\n".join(result)

    def _condense_config_content(self, content: str, level: str) -> str:
        """Condense configuration file content."""
        if level == CondensingLevel.LIGHT:
            return content  # Config files are usually already concise

        # For config files, show structure overview
        try:
            import json

            import yaml

            # Try to parse as JSON first
            try:
                data = json.loads(content)
                return self._summarize_json_structure(data, level)
            except json.JSONDecodeError:
                pass

            # Try YAML
            try:
                data = yaml.safe_load(content)
                return self._summarize_yaml_structure(data, level)
            except Exception:  # nosec B110
                pass

        except ImportError:
            pass

        # Fall back to line-based summary
        lines = content.split("\n")
        if len(lines) <= 20:
            return content
        else:
            return "\n".join(lines[:10] + ["# ... truncated ..."] + lines[-5:])

    def _condense_generic_content(self, content: str, level: str) -> str:
        """Generic condensing for unknown file types."""
        lines = content.split("\n")

        if level == CondensingLevel.LIGHT:
            # Remove empty lines and comments
            return "\n".join(
                line
                for line in lines
                if line.strip() and not line.strip().startswith("#")
            )

        elif level == CondensingLevel.MODERATE:
            # Keep first 20 and last 10 lines
            if len(lines) <= 30:
                return content
            return "\n".join(lines[:20] + ["# ... content truncated ..."] + lines[-10:])

        else:
            # Heavy or maximum: just show first few lines
            return "\n".join(lines[:10] + ["# ... heavily truncated ..."])

    # Helper methods for Python condensing

    def _get_source_segment(self, lines: list[str], node: ast.AST) -> str:
        """Get source code segment for an AST node."""
        if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
            start = max(0, node.lineno - 1)
            end = min(len(lines), node.end_lineno)
            return "\n".join(lines[start:end])
        return ""

    def _get_function_signature(self, node: ast.FunctionDef, lines: list[str]) -> str:
        """Extract function signature from AST node."""
        if hasattr(node, "lineno"):
            line_no = node.lineno - 1
            if line_no < len(lines):
                # Find the complete function definition (might span multiple lines)
                signature_lines = []
                i = line_no
                while i < len(lines):
                    line = lines[i]
                    signature_lines.append(line)
                    if ":" in line:
                        break
                    i += 1
                return "\n".join(signature_lines)
        return f"def {node.name}(...):"

    def _get_class_signature(self, node: ast.ClassDef, lines: list[str]) -> str:
        """Extract class signature from AST node."""
        if hasattr(node, "lineno"):
            line_no = node.lineno - 1
            if line_no < len(lines):
                return lines[line_no]
        return f"class {node.name}:"

    def _condense_python_class(
        self, node: ast.ClassDef, lines: list[str], priority: PriorityLevel
    ) -> list[str]:
        """Condense a Python class preserving important methods."""
        result = []

        # Class signature
        result.append(self._get_class_signature(node, lines))

        # Class docstring for important classes
        docstring = ast.get_docstring(node)
        if docstring and priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]:
            result.append(f'    """{docstring}"""')

        # Important methods
        important_methods = [
            "__init__",
            "__call__",
            "__enter__",
            "__exit__",
            "main",
            "run",
            "execute",
        ]
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name in important_methods or priority == PriorityLevel.CRITICAL:
                    method_sig = self._get_function_signature(item, lines)
                    # Indent method signature
                    indented = "\n".join(
                        "    " + line for line in method_sig.split("\n")
                    )
                    result.append(indented)

        return result

    def _condense_python_function(
        self, node: ast.FunctionDef, lines: list[str], priority: PriorityLevel
    ) -> list[str]:
        """Condense a Python function preserving signature and docstring."""
        result = []

        # Function signature
        result.append(self._get_function_signature(node, lines))

        # Function docstring for important functions
        docstring = ast.get_docstring(node)
        if docstring and priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]:
            result.append(f'    """{docstring}"""')

        return result

    def _summarize_json_structure(self, data, level: str) -> str:
        """Summarize JSON structure."""
        if level == CondensingLevel.MODERATE:
            return self._describe_data_structure(data, max_depth=2)
        else:
            return self._describe_data_structure(data, max_depth=1)

    def _summarize_yaml_structure(self, data, level: str) -> str:
        """Summarize YAML structure."""
        return self._summarize_json_structure(data, level)

    def _describe_data_structure(
        self, data, max_depth: int, current_depth: int = 0
    ) -> str:
        """Describe the structure of nested data."""
        if current_depth >= max_depth:
            return f"<{type(data).__name__}>"

        if isinstance(data, dict):
            if not data:
                return "{}"
            items = []
            for key, value in list(data.items())[:5]:  # Limit to first 5 keys
                value_desc = self._describe_data_structure(
                    value, max_depth, current_depth + 1
                )
                items.append(f'"{key}": {value_desc}')
            if len(data) > 5:
                items.append("...")
            return "{" + ", ".join(items) + "}"

        elif isinstance(data, list):
            if not data:
                return "[]"
            if len(data) == 1:
                item_desc = self._describe_data_structure(
                    data[0], max_depth, current_depth + 1
                )
                return f"[{item_desc}]"
            else:
                first_desc = self._describe_data_structure(
                    data[0], max_depth, current_depth + 1
                )
                return f"[{first_desc}, ...] (length: {len(data)})"

        else:
            return (
                f"{type(data).__name__}({repr(data)[:20]}...)"
                if len(repr(data)) > 20
                else repr(data)
            )

    def _increase_condensing_level(self, current_level: str) -> str:
        """Increase condensing aggressiveness."""
        levels = [
            CondensingLevel.NONE,
            CondensingLevel.LIGHT,
            CondensingLevel.MODERATE,
            CondensingLevel.HEAVY,
            CondensingLevel.MAXIMUM,
        ]
        try:
            current_index = levels.index(current_level)
            return levels[min(current_index + 1, len(levels) - 1)]
        except ValueError:
            return CondensingLevel.MODERATE

    def _decrease_condensing_level(self, current_level: str) -> str:
        """Decrease condensing aggressiveness."""
        levels = [
            CondensingLevel.NONE,
            CondensingLevel.LIGHT,
            CondensingLevel.MODERATE,
            CondensingLevel.HEAVY,
            CondensingLevel.MAXIMUM,
        ]
        try:
            current_index = levels.index(current_level)
            return levels[max(current_index - 1, 0)]
        except ValueError:
            return CondensingLevel.MODERATE

    def _condense_function_preserve_structure(
        self, function_content: str, language: str
    ) -> str:
        """Condense function while preserving logical structure."""
        if language == "python":
            # For Python, try to preserve the signature and key statements
            lines = function_content.split("\n")
            result = []
            in_docstring = False
            docstring_quotes = None

            for line in lines:
                stripped = line.strip()

                # Always keep function signature
                if stripped.startswith("def ") or stripped.startswith("async def "):
                    result.append(line)
                    continue

                # Handle docstrings
                if not in_docstring and ('"""' in line or "'''" in line):
                    docstring_quotes = '"""' if '"""' in line else "'''"
                    in_docstring = True
                    result.append(line)
                    if line.count(docstring_quotes) >= 2:  # Single line docstring
                        in_docstring = False
                    continue
                elif in_docstring:
                    result.append(line)
                    if docstring_quotes and docstring_quotes in line:
                        in_docstring = False
                    continue

                # Keep important statements
                if any(
                    keyword in stripped
                    for keyword in ["return", "raise", "yield", "assert"]
                ):
                    result.append(line)
                elif stripped.startswith(
                    (
                        "if ",
                        "elif ",
                        "else:",
                        "for ",
                        "while ",
                        "try:",
                        "except",
                        "finally:",
                    )
                ):
                    result.append(line)
                elif stripped and not stripped.startswith("#"):
                    # Keep one example of regular statements
                    result.append("    # ... implementation details ...")
                    break

            return "\n".join(result)
        else:
            # For other languages, just preserve first and last few lines
            lines = function_content.split("\n")
            if len(lines) <= 10:
                return function_content
            return "\n".join(lines[:5] + ["    // ... implementation ..."] + lines[-2:])

    def _condense_function_minimal(self, function_content: str, language: str) -> str:
        """Minimally condense function to just signature."""
        lines = function_content.split("\n")

        if language == "python":
            for line in lines:
                if line.strip().startswith(("def ", "async def ")):
                    return line + "\n    # ... implementation ..."
        else:
            # For other languages, find function declaration
            for line in lines:
                if any(
                    keyword in line
                    for keyword in ["function", "def", "public", "private"]
                ):
                    return line + "\n    // ... implementation ..."

        return function_content.split("\n")[0] + "\n    # ..."
