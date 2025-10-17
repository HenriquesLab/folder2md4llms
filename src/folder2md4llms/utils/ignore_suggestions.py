"""Intelligent ignore pattern suggestions based on file analysis."""

import sys
from pathlib import Path

import click
from rich.console import Console

console = Console()


class IgnoreSuggester:
    """Suggests ignore patterns based on file patterns and sizes."""

    def __init__(
        self,
        min_file_size: int = 100_000,
        min_dir_size: int = 1_000_000,
        large_file_threshold: int = 10_485_760,  # 10MB
        ignore_patterns=None,
    ):
        """Initialize the suggester with size thresholds.

        Args:
            min_file_size: Minimum file size in bytes to suggest ignoring
            min_dir_size: Minimum directory size in bytes to suggest ignoring
            large_file_threshold: Size threshold for flagging large files (default: 10MB)
            ignore_patterns: IgnorePatterns instance to check if files are already ignored
        """
        self.min_file_size = min_file_size
        self.min_dir_size = min_dir_size
        self.large_file_threshold = large_file_threshold
        self.ignore_patterns = ignore_patterns
        self.base_path: Path | None = None
        self.suggestions: dict[str, set[str]] = {}
        self.file_details: dict[
            str, dict
        ] = {}  # Store file details for interactive prompts

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
            file_name = file_path.name
            extension = file_path.suffix.lower()

            # Check for binary data files (always suggest regardless of size)
            if self._is_binary_data_file(file_name, extension):
                pattern = f"*{extension}" if extension else file_name
                self._add_suggestion(
                    "binary_data",
                    pattern,
                    f"Binary data file: {file_name} ({self._format_size(file_size)})",
                    file_size,
                )
                return

            # Check for media files (always suggest regardless of size)
            if self._is_media_file(extension):
                pattern = f"*{extension}"
                self._add_suggestion(
                    "media_files",
                    pattern,
                    f"Media file: {file_name} ({self._format_size(file_size)})",
                    file_size,
                )
                return

            # Check for build artifacts (always suggest regardless of size)
            if self._is_build_artifact(file_name, extension):
                pattern = (
                    f"*{extension}"
                    if extension and extension != ".js" and extension != ".css"
                    else file_name
                )
                self._add_suggestion(
                    "build_artifacts",
                    pattern,
                    f"Build artifact: {file_name} ({self._format_size(file_size)})",
                    file_size,
                )
                return

            # Check for large files
            if file_size >= self.large_file_threshold:
                self._add_suggestion(
                    "large_files",
                    file_name,
                    f"Large file: {file_name} ({self._format_size(file_size)})",
                    file_size,
                )
                return

            # Existing checks for files above min_file_size
            if file_size < self.min_file_size:
                return

            # Check for cache-like patterns
            if self._is_cache_like(file_name):
                self._add_suggestion(
                    "cache_files",
                    file_name,
                    f"Large cache file: {file_name} ({self._format_size(file_size)})",
                    file_size,
                )

            # Check for hidden files that are large
            elif file_name.startswith("."):
                self._add_suggestion(
                    "hidden_files",
                    file_name,
                    f"Large hidden file: {file_name} ({self._format_size(file_size)})",
                    file_size,
                )

            # Check for temporary files
            elif self._is_temp_like(file_name):
                self._add_suggestion(
                    "temp_files",
                    file_name,
                    f"Large temporary file: {file_name} ({self._format_size(file_size)})",
                    file_size,
                )

            # Check for backup files
            elif self._is_backup_like(file_name):
                self._add_suggestion(
                    "backup_files",
                    file_name,
                    f"Large backup file: {file_name} ({self._format_size(file_size)})",
                    file_size,
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

    def _is_binary_data_file(self, name: str, extension: str) -> bool:
        """Check if file is a binary data format (scientific data, serialized objects, etc.)."""
        binary_data_extensions = {
            # Scientific data formats
            ".cif",  # Crystallographic Information File
            ".h5",
            ".hdf5",  # HDF5
            ".mat",  # MATLAB
            ".npy",
            ".npz",  # NumPy
            ".fits",  # Astronomy data
            ".nc",
            ".nc4",  # NetCDF
            ".zarr",  # Zarr
            # Serialization formats
            ".pkl",
            ".pickle",  # Python pickle
            ".parquet",  # Apache Parquet
            ".feather",  # Apache Feather
            ".arrow",  # Apache Arrow
            ".avro",  # Apache Avro
            # Database files
            ".db",
            ".sqlite",
            ".sqlite3",
            ".mdb",
            ".accdb",  # MS Access
            # Other binary formats
            ".bin",
            ".dat",
        }
        return extension in binary_data_extensions

    def _is_media_file(self, extension: str) -> bool:
        """Check if file is a media file (image, video, audio)."""
        media_extensions = {
            # Images
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
            ".tiff",
            ".tif",
            ".webp",
            ".ico",
            ".svg",
            ".raw",
            ".cr2",
            ".nef",
            ".arw",
            ".dng",
            ".orf",
            ".sr2",
            ".psd",
            # Videos
            ".mp4",
            ".avi",
            ".mov",
            ".mkv",
            ".flv",
            ".wmv",
            ".webm",
            ".m4v",
            ".mpg",
            ".mpeg",
            ".3gp",
            # Audio
            ".mp3",
            ".wav",
            ".flac",
            ".aac",
            ".ogg",
            ".m4a",
            ".wma",
            ".opus",
            ".ape",
            ".alac",
        }
        return extension in media_extensions

    def _is_build_artifact(self, name: str, extension: str) -> bool:
        """Check if file is a build artifact (compiled code, minified files, etc.)."""
        # Build artifact extensions
        build_extensions = {
            ".pyc",
            ".pyo",  # Python bytecode
            ".so",
            ".dylib",
            ".dll",  # Shared libraries
            ".exe",
            ".bin",  # Executables
            ".whl",
            ".egg",  # Python packages
            ".jar",
            ".class",  # Java
            ".o",
            ".obj",  # Object files
            ".a",
            ".lib",  # Static libraries
        }

        # Check extension
        if extension in build_extensions:
            return True

        # Check for minified JS/CSS
        name_lower = name.lower()
        if name_lower.endswith(".min.js") or name_lower.endswith(".min.css"):
            return True

        # Check for common build artifact patterns
        build_patterns = [
            "dist/",
            "build/",
            ".next/",
            ".nuxt/",
            "target/",
            "__pycache__/",
            "node_modules/",
        ]

        return any(pattern in name_lower for pattern in build_patterns)

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

    def _add_suggestion(
        self, category: str, pattern: str, reason: str, file_size: int = 0
    ) -> None:
        """Add a suggestion to the appropriate category."""
        if category not in self.suggestions:
            self.suggestions[category] = set()

        self.suggestions[category].add(pattern)

        # Store file details for interactive prompts
        if pattern not in self.file_details:
            self.file_details[pattern] = {
                "category": category,
                "size": file_size,
                "count": 0,
            }
        self.file_details[pattern]["count"] += 1
        self.file_details[pattern]["size"] += file_size

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
            "binary_data": "📊 Binary Data Files",
            "media_files": "🎬 Media Files",
            "build_artifacts": "🔨 Build Artifacts",
            "large_files": "📦 Large Files",
            "cache_files": "💾 Cache Files",
            "cache_dirs": "💾 Cache Directories",
            "hidden_files": "🔒 Large Hidden Files",
            "hidden_dirs": "🔒 Large Hidden Directories",
            "temp_files": "🗑️ Temporary Files",
            "temp_dirs": "🗑️ Temporary Directories",
            "backup_files": "💼 Backup Files",
            "backup_dirs": "💼 Backup Directories",
        }

        # Define priority order for categories
        category_order = [
            "binary_data",
            "media_files",
            "build_artifacts",
            "large_files",
            "cache_files",
            "cache_dirs",
            "temp_files",
            "temp_dirs",
            "backup_files",
            "backup_dirs",
            "hidden_files",
            "hidden_dirs",
        ]

        for category in category_order:
            if category in self.suggestions and self.suggestions[category]:
                category_name = category_names.get(category, category)
                suggestions.append((category_name, sorted(self.suggestions[category])))

        # Add any remaining categories not in the order
        for category, patterns in self.suggestions.items():
            if patterns and category not in category_order:
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

    def prompt_and_apply_suggestions(
        self, ignore_file_path: Path, base_path: Path
    ) -> None:
        """Interactively prompt user and apply selected suggestions to ignore file."""
        suggestions = self.get_suggestions()

        if not suggestions:
            return

        # Skip interactive prompts in non-interactive environments
        if not sys.stdin.isatty():
            console.print()
            console.print(
                "[yellow]💡 Non-interactive environment: Skipping ignore suggestions[/yellow]"
            )
            console.print(
                "[yellow]Run with --verbose to see suggestions, or run interactively to apply them.[/yellow]"
            )
            return

        console.print()
        console.print("💡 [bold yellow]Ignore Pattern Suggestions[/bold yellow]")
        console.print("Found files that might not be useful for LLM analysis:")
        console.print()

        patterns_to_add = []

        for category_name, patterns in suggestions:
            # Calculate total size for this category
            total_size = sum(
                self.file_details.get(p, {}).get("size", 0) for p in patterns
            )
            total_count = sum(
                self.file_details.get(p, {}).get("count", 0) for p in patterns
            )

            console.print(f"  [bold cyan]{category_name}[/bold cyan]")
            if total_size > 0:
                console.print(
                    f"    Total: {self._format_size(total_size)} across {total_count} file(s)"
                )

            for pattern in patterns:
                details = self.file_details.get(pattern, {})
                size = details.get("size", 0)
                count = details.get("count", 0)
                if size > 0:
                    if count > 1:
                        console.print(
                            f"      • {pattern} ({count} files, {self._format_size(size)})"
                        )
                    else:
                        console.print(f"      • {pattern} ({self._format_size(size)})")
                else:
                    console.print(f"      • {pattern}")

            console.print()

            # Ask user if they want to add this category to ignore
            try:
                if click.confirm(
                    f"  Add pattern(s) from '{category_name}' to .folder2md_ignore?",
                    default=True,
                ):
                    patterns_to_add.extend(patterns)
                    console.print(
                        f"  [green]✓ Will add {len(patterns)} pattern(s)[/green]"
                    )
                else:
                    console.print("  [yellow]⊘ Skipped[/yellow]")
                console.print()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Interrupted. No patterns added.[/yellow]")
                return

        if not patterns_to_add:
            console.print("[yellow]No patterns selected.[/yellow]")
            return

        # Apply patterns to ignore file
        try:
            # Read existing content if file exists
            existing_content = ""
            if ignore_file_path.exists():
                existing_content = ignore_file_path.read_text(encoding="utf-8")

            # Prepare new content
            new_patterns = []
            for pattern in patterns_to_add:
                # Check if pattern already exists
                if pattern not in existing_content:
                    new_patterns.append(pattern)

            if new_patterns:
                # Create or append to ignore file
                with open(ignore_file_path, "a", encoding="utf-8") as f:
                    if existing_content and not existing_content.endswith("\n"):
                        f.write("\n")
                    f.write("\n# Suggested by folder2md4llms\n")
                    for pattern in new_patterns:
                        f.write(f"{pattern}\n")

                console.print(
                    f"[green]✓ Added {len(new_patterns)} pattern(s) to {ignore_file_path}[/green]"
                )
                console.print(
                    "[cyan]These patterns will be ignored in future runs.[/cyan]"
                )
            else:
                console.print(
                    "[yellow]All suggested patterns already exist in ignore file.[/yellow]"
                )

        except Exception as e:
            console.print(f"[red]Error updating ignore file: {e}[/red]")
            console.print(
                "[yellow]You can manually add these patterns to .folder2md_ignore[/yellow]"
            )
