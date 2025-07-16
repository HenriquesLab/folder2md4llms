"""Markdown formatter for repository contents."""

from pathlib import Path
from typing import Dict, Optional

from pygments.lexers import guess_lexer_for_filename
from pygments.util import ClassNotFound

from ..utils.file_utils import get_language_from_extension


class MarkdownFormatter:
    """Formats repository contents as markdown."""

    def __init__(self, include_tree: bool = True, include_stats: bool = True):
        self.include_tree = include_tree
        self.include_stats = include_stats
        # We don't need pygments formatter for markdown output - we'll format manually

    def format_repository(
        self,
        repo_path: Path,
        tree_structure: Optional[str] = None,
        file_contents: Optional[Dict[str, str]] = None,
        file_stats: Optional[Dict] = None,
        binary_descriptions: Optional[Dict[str, str]] = None,
        converted_docs: Optional[Dict[str, str]] = None,
    ) -> str:
        """Format the complete repository as markdown."""
        sections = []

        # Header
        repo_name = repo_path.name
        sections.append(f"# Repository: {repo_name}")
        sections.append("")

        # Table of Contents
        sections.append("## 📑 Table of Contents")
        if self.include_tree:
            sections.append("- [📁 Folder Structure](#-folder-structure)")
        if self.include_stats:
            sections.append("- [📊 Repository Statistics](#-repository-statistics)")
        if file_contents:
            sections.append("- [📄 Source Code](#-source-code)")
        if converted_docs:
            sections.append("- [📋 Documents](#-documents)")
        if binary_descriptions:
            sections.append("- [🔧 Binary Files & Assets](#-binary-files--assets)")
        sections.append("")

        # Folder Structure
        if self.include_tree and tree_structure:
            sections.append("## 📁 Folder Structure")
            sections.append("```")
            sections.append(tree_structure)
            sections.append("```")
            sections.append("")

        # Repository Statistics
        if self.include_stats and file_stats:
            sections.append("## 📊 Repository Statistics")
            sections.append(self._format_stats(file_stats))
            sections.append("")

        # Source Code Files
        if file_contents:
            sections.append("## 📄 Source Code")
            sections.append("")
            for file_path, content in file_contents.items():
                sections.append(self._format_file_content(file_path, content))
                sections.append("")

        # Converted Documents
        if converted_docs:
            sections.append("## 📋 Documents")
            sections.append("")
            for file_path, content in converted_docs.items():
                sections.append(self._format_document_content(file_path, content))
                sections.append("")

        # Binary Files
        if binary_descriptions:
            sections.append("## 🔧 Binary Files & Assets")
            sections.append("")
            for file_path, description in binary_descriptions.items():
                sections.append(self._format_binary_description(file_path, description))
                sections.append("")

        return "\n".join(sections)

    def _format_stats(self, stats: Dict) -> str:
        """Format repository statistics."""
        lines = []

        # File counts
        lines.append("### File Counts")
        lines.append(f"- **Total Files:** {stats.get('total_files', 0)}")
        lines.append(f"- **Text Files:** {stats.get('text_files', 0)}")
        lines.append(f"- **Binary Files:** {stats.get('binary_files', 0)}")
        lines.append(f"- **Converted Documents:** {stats.get('converted_docs', 0)}")
        lines.append("")

        # Size information
        if "total_size" in stats:
            lines.append("### Size Information")
            lines.append(f"- **Total Size:** {self._format_size(stats['total_size'])}")
            lines.append(
                f"- **Text Content:** {self._format_size(stats.get('text_size', 0))}"
            )
            lines.append("")

        # Language breakdown
        if "languages" in stats:
            lines.append("### Languages")
            languages = stats["languages"]
            for lang, count in sorted(
                languages.items(), key=lambda x: x[1], reverse=True
            ):
                lines.append(f"- **{lang}:** {count} files")
            lines.append("")

        return "\n".join(lines)

    def _format_file_content(self, file_path: str, content: str) -> str:
        """Format a single file's content with syntax highlighting."""
        lines = []

        # File header
        lines.append(f"### 📄 `{file_path}`")
        lines.append("")

        # Detect language for syntax highlighting
        language = self._detect_language(file_path, content)

        # Add syntax-highlighted content
        if language:
            lines.append(f"```{language}")
        else:
            lines.append("```")

        lines.append(content.rstrip())
        lines.append("```")

        return "\n".join(lines)

    def _format_document_content(self, file_path: str, content: str) -> str:
        """Format a converted document's content."""
        lines = []

        # Document header
        lines.append(f"### 📋 `{file_path}`")
        lines.append("")

        # Add converted content
        lines.append(content.rstrip())

        return "\n".join(lines)

    def _format_binary_description(self, file_path: str, description: str) -> str:
        """Format a binary file description."""
        lines = []

        # Binary file header
        lines.append(f"### 🔧 `{file_path}`")
        lines.append("")
        lines.append(description.rstrip())

        return "\n".join(lines)

    def _detect_language(self, file_path: str, content: str) -> Optional[str]:
        """Detect the programming language for syntax highlighting."""
        try:
            # Try to guess from filename
            lexer = guess_lexer_for_filename(file_path, content)
            return lexer.aliases[0] if lexer.aliases else None
        except ClassNotFound:
            # Fall back to extension-based detection
            return get_language_from_extension(Path(file_path).suffix.lower())

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
