"""Intelligent ignore pattern suggestions based on file analysis."""

from pathlib import Path

from rich.console import Console

console = Console()


class IgnoreSuggester:
    """Suggests ignore patterns based on file patterns and sizes."""

    def __init__(
        self,
        min_file_size: int = 100_000,
        min_dir_size: int = 1_000_000,
        ignore_patterns=None,
    ):
        """Initialize the suggester with size thresholds.

        Args:
            min_file_size: Minimum file size in bytes to suggest ignoring
            min_dir_size: Minimum directory size in bytes to suggest ignoring
            ignore_patterns: IgnorePatterns instance to check if files are already ignored
        """
        self.min_file_size = min_file_size
        self.min_dir_size = min_dir_size
        self.ignore_patterns = ignore_patterns
        self.base_path: Path | None = None
        self.suggestions: dict[str, set[str]] = {}

    def analyze_path(self, path: Path, base_path: Path | None = None) -> None:
        """Analyze a path and collect suggestions."""
        if not path.exists():
            return

        # Set base path for ignore pattern checking
        if base_path is not None:
            self.base_path = base_path

        # Skip if already ignored
        if self.ignore_patterns and self.base_path:
            try:
                if self.ignore_patterns.should_ignore(path, self.base_path):
                    return
            except (ValueError, OSError):
                # If we can't check ignore status, continue with analysis
                pass

        if path.is_file():
            self._analyze_file(path)
        elif path.is_dir():
            self._analyze_directory(path)

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single file for ignore suggestions."""
        try:
            file_size = file_path.stat().st_size

            if file_size < self.min_file_size:
                return

            file_name = file_path.name

            # Check for cache-like patterns
            if self._is_cache_like(file_name):
                self._add_suggestion(
                    "cache_files",
                    file_name,
                    f"Large cache file: {file_name} ({self._format_size(file_size)})",
                )

            # Check for hidden files that are large
            elif file_name.startswith("."):
                self._add_suggestion(
                    "hidden_files",
                    file_name,
                    f"Large hidden file: {file_name} ({self._format_size(file_size)})",
                )

            # Check for temporary files
            elif self._is_temp_like(file_name):
                self._add_suggestion(
                    "temp_files",
                    file_name,
                    f"Large temporary file: {file_name} ({self._format_size(file_size)})",
                )

            # Check for backup files
            elif self._is_backup_like(file_name):
                self._add_suggestion(
                    "backup_files",
                    file_name,
                    f"Large backup file: {file_name} ({self._format_size(file_size)})",
                )

        except (OSError, PermissionError):
            # Skip files we can't access
            pass

    def _analyze_directory(self, dir_path: Path) -> None:
        """Analyze a directory for ignore suggestions."""
        try:
            dir_size = self._get_directory_size(dir_path)

            if dir_size < self.min_dir_size:
                return

            dir_name = dir_path.name

            # Check for cache-like directories
            if self._is_cache_like(dir_name):
                self._add_suggestion(
                    "cache_dirs",
                    f"{dir_name}/",
                    f"Large cache directory: {dir_name}/ ({self._format_size(dir_size)})",
                )

            # Check for hidden directories
            elif dir_name.startswith("."):
                self._add_suggestion(
                    "hidden_dirs",
                    f"{dir_name}/",
                    f"Large hidden directory: {dir_name}/ ({self._format_size(dir_size)})",
                )

            # Check for temporary directories
            elif self._is_temp_like(dir_name):
                self._add_suggestion(
                    "temp_dirs",
                    f"{dir_name}/",
                    f"Large temporary directory: {dir_name}/ ({self._format_size(dir_size)})",
                )

            # Check for backup directories
            elif self._is_backup_like(dir_name):
                self._add_suggestion(
                    "backup_dirs",
                    f"{dir_name}/",
                    f"Large backup directory: {dir_name}/ ({self._format_size(dir_size)})",
                )

        except (OSError, PermissionError):
            # Skip directories we can't access
            pass

    def _is_cache_like(self, name: str) -> bool:
        """Check if name looks like a cache file/directory."""
        cache_patterns = [
            "cache",
            "cached",
            ".cache",
            "__pycache__",
            "tmp",
            "temp",
            ".tmp",
            ".temp",
            "log",
            "logs",
            ".log",
            ".logs",
            "coverage",
            ".coverage",
            ".nyc_output",
            "jest",
            ".jest",
            "pytest_cache",
            ".pytest_cache",
            "mypy_cache",
            ".mypy_cache",
            "ruff_cache",
            ".ruff_cache",
            "tox",
            ".tox",
            "nox",
            ".nox",
            "htmlcov",
            "cov_html",
            "coverage_html",
        ]

        name_lower = name.lower()
        return any(pattern in name_lower for pattern in cache_patterns)

    def _is_temp_like(self, name: str) -> bool:
        """Check if name looks like a temporary file/directory."""
        temp_patterns = [
            "tmp",
            "temp",
            "temporary",
            "scratch",
            "work",
            ".tmp",
            ".temp",
            ".temporary",
            ".scratch",
            ".work",
        ]

        name_lower = name.lower()
        return any(pattern in name_lower for pattern in temp_patterns)

    def _is_backup_like(self, name: str) -> bool:
        """Check if name looks like a backup file/directory."""
        backup_patterns = [
            "backup",
            "backups",
            "bak",
            ".bak",
            ".backup",
            "old",
            ".old",
            "orig",
            ".orig",
            "save",
            ".save",
            "copy",
            ".copy",
            "archive",
            ".archive",
        ]

        name_lower = name.lower()
        return any(
            pattern in name_lower for pattern in backup_patterns
        ) or name.endswith("~")

    def _get_directory_size(self, dir_path: Path) -> int:
        """Get the total size of a directory."""
        total_size = 0
        try:
            for item in dir_path.rglob("*"):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass
        return total_size

    def _add_suggestion(self, category: str, pattern: str, reason: str) -> None:
        """Add a suggestion to the appropriate category."""
        if category not in self.suggestions:
            self.suggestions[category] = set()

        self.suggestions[category].add(pattern)

    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        size_float = float(size)
        for unit in ["B", "KB", "MB", "GB"]:
            if size_float < 1024.0:
                return f"{size_float:.1f} {unit}"
            size_float = size_float / 1024.0
        return f"{size_float:.1f} TB"

    def get_suggestions(self) -> list[tuple[str, list[str]]]:
        """Get all suggestions grouped by category."""
        suggestions = []

        category_names = {
            "cache_files": "Cache Files",
            "cache_dirs": "Cache Directories",
            "hidden_files": "Large Hidden Files",
            "hidden_dirs": "Large Hidden Directories",
            "temp_files": "Temporary Files",
            "temp_dirs": "Temporary Directories",
            "backup_files": "Backup Files",
            "backup_dirs": "Backup Directories",
        }

        for category, patterns in self.suggestions.items():
            if patterns:
                category_name = category_names.get(category, category)
                suggestions.append((category_name, sorted(patterns)))

        return suggestions

    def display_suggestions(self, output_file: Path) -> None:
        """Display suggestions to the user."""
        suggestions = self.get_suggestions()

        if not suggestions:
            return

        console.print()
        console.print("💡 [bold yellow]Ignore Suggestions[/bold yellow]")
        console.print(
            "The following files/directories might be worth adding to your .folder2md_ignore:"
        )
        console.print()

        for category, patterns in suggestions:
            console.print(f"  [bold cyan]{category}:[/bold cyan]")
            for pattern in patterns:
                console.print(f"    • {pattern}")
            console.print()

        ignore_file = output_file.parent / ".folder2md_ignore"
        console.print(
            f"📝 Add these patterns to [bold]{ignore_file}[/bold] to exclude them from future runs."
        )
        console.print()
