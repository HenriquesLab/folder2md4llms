"""Base code analyzer for extracting structure from various programming languages."""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseCodeAnalyzer(ABC):
    """Base class for code analyzers that extract structure from source code files."""

    def __init__(self, condense_mode: str = "signatures_with_docstrings"):
        """Initialize the code analyzer.

        Args:
            condense_mode: How to condense the code
                - "signatures": Function/class signatures only
                - "signatures_with_docstrings": Signatures plus docstrings
                - "structure": Full structure with comments and type information
        """
        self.condense_mode = condense_mode

    @abstractmethod
    def analyze_file(self, file_path: Path) -> str | None:
        """Analyze a source code file and return condensed content.

        Args:
            file_path: Path to the source code file

        Returns:
            Condensed code content or None if analysis failed
        """
        pass

    @abstractmethod
    def analyze_code(self, content: str, filename: str = "<string>") -> str | None:
        """Analyze source code content and return condensed version.

        Args:
            content: Source code content
            filename: Filename for error reporting

        Returns:
            Condensed code content or None if parsing failed
        """
        pass

    @abstractmethod
    def get_supported_extensions(self) -> set[str]:
        """Get the file extensions this analyzer supports.

        Returns:
            Set of supported file extensions
        """
        pass

    def _extract_imports(self, content: str) -> list[str]:
        """Extract import statements from source code.

        Args:
            content: Source code content

        Returns:
            List of import statements
        """
        # Default implementation - override in language-specific analyzers
        return []

    def _extract_functions(self, content: str) -> list[dict[str, Any]]:
        """Extract function definitions from source code.

        Args:
            content: Source code content

        Returns:
            List of function information dictionaries
        """
        # Default implementation - override in language-specific analyzers
        return []

    def _extract_classes(self, content: str) -> list[dict[str, Any]]:
        """Extract class definitions from source code.

        Args:
            content: Source code content

        Returns:
            List of class information dictionaries
        """
        # Default implementation - override in language-specific analyzers
        return []

    def _extract_comments(self, content: str) -> list[str]:
        """Extract significant comments (like file headers).

        Args:
            content: Source code content

        Returns:
            List of significant comments
        """
        # Default implementation - override in language-specific analyzers
        return []

    def _clean_content(self, content: str) -> str:
        """Clean and prepare content for analysis.

        Args:
            content: Raw file content

        Returns:
            Cleaned content
        """
        # Remove excessive whitespace
        lines = content.splitlines()
        cleaned_lines = []

        for line in lines:
            # Keep the line but strip trailing whitespace
            cleaned_lines.append(line.rstrip())

        return "\n".join(cleaned_lines)

    def _format_header(self, file_path: Path, language: str) -> str:
        """Format the analysis header for output.

        Args:
            file_path: Path to the analyzed file
            language: Programming language

        Returns:
            Formatted header string
        """
        return f"""# {language.title()} Code Analysis: {file_path.name}
# Condensed using mode: {self.condense_mode}
# Original file: {file_path}

"""

    def _indent_text(self, text: str, spaces: int) -> str:
        """Indent text by specified number of spaces.

        Args:
            text: Text to indent
            spaces: Number of spaces to indent

        Returns:
            Indented text
        """
        indent = " " * spaces
        lines = text.split("\n")
        return "\n".join(indent + line if line.strip() else line for line in lines)

    def _truncate_list(
        self, items: list[Any], max_items: int = 10, item_name: str = "items"
    ) -> list[Any]:
        """Truncate a list and add a note if truncated.

        Args:
            items: List to potentially truncate
            max_items: Maximum number of items to keep
            item_name: Name of items for truncation message

        Returns:
            Truncated list with optional truncation note
        """
        if len(items) <= max_items:
            return items

        truncated = items[:max_items]
        truncated.append(f"# ... and {len(items) - max_items} more {item_name}")
        return truncated

    def _should_include_docstring(self) -> bool:
        """Check if docstrings should be included based on condense mode.

        Returns:
            True if docstrings should be included
        """
        return self.condense_mode in ["signatures_with_docstrings", "structure"]

    def _should_include_comments(self) -> bool:
        """Check if comments should be included based on condense mode.

        Returns:
            True if comments should be included
        """
        return self.condense_mode == "structure"

    def get_stats(self) -> dict[str, Any]:
        """Get analysis statistics.

        Returns:
            Dictionary with analysis statistics
        """
        return {
            "condense_mode": self.condense_mode,
            "analyzer_type": self.__class__.__name__.lower(),
            "supported_extensions": list(self.get_supported_extensions()),
        }


class RegexBasedAnalyzer(BaseCodeAnalyzer):
    """Base class for analyzers that use regex patterns to extract code structure."""

    def __init__(self, condense_mode: str = "signatures_with_docstrings"):
        super().__init__(condense_mode)
        self.function_pattern: re.Pattern | None = None
        self.class_pattern: re.Pattern | None = None
        self.import_pattern: re.Pattern | None = None
        self.comment_pattern: re.Pattern | None = None

    @abstractmethod
    def _compile_patterns(self) -> None:
        """Compile regex patterns for the specific language."""
        pass

    def analyze_file(self, file_path: Path) -> str | None:
        """Analyze a source code file and return condensed content."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            return self.analyze_code(content, str(file_path))
        except (OSError, UnicodeDecodeError) as e:
            return f"# Error reading file: {e}"

    def analyze_code(self, content: str, filename: str = "<string>") -> str | None:
        """Analyze source code content and return condensed version."""
        try:
            # Ensure patterns are compiled
            if self.function_pattern is None:
                self._compile_patterns()

            content = self._clean_content(content)
            result = []

            # Add header
            language = self.__class__.__name__.replace("Analyzer", "").lower()
            result.append(self._format_header(Path(filename), language))

            # Extract and add components
            imports = self._extract_imports(content)
            if imports:
                result.extend(self._truncate_list(imports, 10, "imports"))
                result.append("")

            classes = self._extract_classes(content)
            functions = self._extract_functions(content)

            # Add classes and functions
            for cls in classes:
                result.append(self._format_class(cls))
                result.append("")

            for func in functions:
                result.append(self._format_function(func))
                result.append("")

            return "\n".join(result)

        except Exception as e:
            return f"# Error parsing {filename}: {e}"

    def _format_class(self, class_info: dict[str, Any]) -> str:
        """Format a class for output.

        Args:
            class_info: Dictionary containing class information

        Returns:
            Formatted class string
        """
        # Default implementation - override in specific analyzers
        return f"class {class_info.get('name', 'Unknown')}: ..."

    def _format_function(self, func_info: dict[str, Any]) -> str:
        """Format a function for output.

        Args:
            func_info: Dictionary containing function information

        Returns:
            Formatted function string
        """
        # Default implementation - override in specific analyzers
        return f"function {func_info.get('name', 'unknown')}(): ..."
