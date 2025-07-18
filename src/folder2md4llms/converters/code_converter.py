"""Multi-language code converter for condensing various programming languages."""

from pathlib import Path

from ..analyzers.config_analyzer import ConfigAnalyzer
from ..analyzers.java_analyzer import JavaAnalyzer
from ..analyzers.javascript_analyzer import JavaScriptAnalyzer
from .base import BaseConverter


class CodeConverter(BaseConverter):
    """Universal code converter that supports multiple programming languages."""

    def __init__(self, config: dict | None = None):
        """Initialize the code converter.

        Args:
            config: Configuration dictionary with optional keys:
                - condense_code: Whether to condense code files
                - code_condense_mode: Mode for condensing
                - condense_languages: List of languages to condense (or "all")
        """
        super().__init__(config)
        self.condense_code = config.get("condense_code", False) if config else False
        self.condense_mode = (
            config.get("code_condense_mode", "signatures_with_docstrings")
            if config
            else "signatures_with_docstrings"
        )

        # Which languages to condense (list of extensions or "all")
        condense_languages = (
            config.get("condense_languages", ["js", "ts", "java"])
            if config
            else ["js", "ts", "java"]
        )
        self.condense_languages = set()

        if condense_languages == "all":
            self.condense_languages = {"all"}
        else:
            # Convert language names to extensions
            for lang in condense_languages:
                if lang in ["js", "javascript"]:
                    self.condense_languages.update([".js", ".jsx", ".mjs", ".cjs"])
                elif lang in ["ts", "typescript"]:
                    self.condense_languages.update([".ts", ".tsx"])
                elif lang in ["java"]:
                    self.condense_languages.add(".java")
                elif lang in ["json"]:
                    self.condense_languages.add(".json")
                elif lang in ["yaml", "yml"]:
                    self.condense_languages.update([".yaml", ".yml"])
                elif lang.startswith("."):
                    self.condense_languages.add(lang)

        # Initialize analyzers
        from typing import Any

        self.analyzers: dict[str, Any] = {}
        if self.condense_code:
            self._initialize_analyzers()

    def _initialize_analyzers(self) -> None:
        """Initialize language-specific analyzers."""
        self.analyzers = {
            "javascript": JavaScriptAnalyzer(self.condense_mode),
            "java": JavaAnalyzer(self.condense_mode),
            "config": ConfigAnalyzer(self.condense_mode),
        }

    def can_convert(self, file_path: Path) -> bool:
        """Check if this converter can handle the file.

        Args:
            file_path: Path to the file

        Returns:
            True if this converter can handle the file and condensing is enabled
        """
        if not self.condense_code:
            return False

        extension = file_path.suffix.lower()

        # Check if this extension should be condensed
        if "all" in self.condense_languages:
            return self._is_supported_extension(extension)
        else:
            return extension in self.condense_languages

    def _is_supported_extension(self, extension: str) -> bool:
        """Check if an extension is supported by any analyzer."""
        for analyzer in self.analyzers.values():
            if extension in analyzer.get_supported_extensions():
                return True
        return False

    def _get_analyzer_for_extension(self, extension: str) -> object | None:
        """Get the appropriate analyzer for a file extension."""
        if extension in [".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"]:
            return self.analyzers.get("javascript")
        elif extension == ".java":
            return self.analyzers.get("java")
        elif extension in [".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"]:
            return self.analyzers.get("config")
        else:
            return None

    def convert(self, file_path: Path) -> str | None:
        """Convert code file to condensed format.

        Args:
            file_path: Path to the code file

        Returns:
            Condensed code or None if conversion failed
        """
        if not self.condense_code:
            return None

        extension = file_path.suffix.lower()
        analyzer = self._get_analyzer_for_extension(extension)

        if not analyzer:
            return None

        try:
            if hasattr(analyzer, "analyze_file"):
                result = analyzer.analyze_file(file_path)
                return result if isinstance(result, str) else None
            return None

        except Exception as e:
            return f"# Error processing {file_path.suffix} file {file_path}: {e}"

    def get_supported_extensions(self) -> set[str]:
        """Get supported file extensions.

        Returns:
            Set of supported file extensions
        """
        if not self.condense_code:
            return set()

        extensions = set()
        for analyzer in self.analyzers.values():
            extensions.update(analyzer.get_supported_extensions())

        # Filter by configured languages if not "all"
        if "all" not in self.condense_languages:
            extensions = extensions.intersection(self.condense_languages)

        return extensions

    def get_conversion_info(self) -> dict:
        """Get information about this converter.

        Returns:
            Dictionary with converter information
        """
        return {
            "name": "Multi-Language Code Analyzer",
            "description": "Extracts signatures and structure from various programming languages",
            "supported_extensions": list(self.get_supported_extensions()),
            "condense_code": self.condense_code,
            "condense_mode": self.condense_mode,
            "condense_languages": list(self.condense_languages),
            "available_analyzers": list(self.analyzers.keys()),
            "dependencies": ["re (built-in)", "json (built-in)", "yaml"],
        }

    def get_analyzer_stats(self) -> dict[str, dict]:
        """Get statistics from all analyzers.

        Returns:
            Dictionary mapping analyzer names to their stats
        """
        stats = {}
        for name, analyzer in self.analyzers.items():
            if hasattr(analyzer, "get_stats"):
                stats[name] = analyzer.get_stats()
        return stats
