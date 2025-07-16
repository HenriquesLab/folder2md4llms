"""Ignore patterns handling for filtering files."""

import fnmatch
import re
from pathlib import Path


class IgnorePatterns:
    """Handles file and directory ignore patterns."""

    DEFAULT_PATTERNS = [
        # Version control
        ".git/",
        ".svn/",
        ".hg/",
        ".bzr/",
        # Build artifacts
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".Python",
        "build/",
        "dist/",
        "*.egg-info/",
        ".eggs/",
        # Dependencies
        "node_modules/",
        "venv/",
        "env/",
        ".venv/",
        "virtualenv/",
        "target/",
        "vendor/",
        # IDE files
        ".vscode/",
        ".idea/",
        "*.sublime-*",
        ".atom/",
        # OS files
        ".DS_Store",
        "**/.DS_Store",
        "Thumbs.db",
        "**/Thumbs.db",
        "desktop.ini",
        "**/desktop.ini",
        # Temporary files
        "*.tmp",
        "*.temp",
        "*.bak",
        "*.backup",
        "*.swp",
        "*.swo",
        "*~",
        # Log files
        "*.log",
        "logs/",
        # Media files (can be large)
        "*.mp4",
        "*.mov",
        "*.avi",
        "*.mkv",
        "*.wmv",
        "*.flv",
        "*.webm",
        "*.mp3",
        "*.wav",
        "*.flac",
        "*.aac",
        "*.ogg",
        "*.wma",
        # Large data files
        "*.zip",
        "*.rar",
        "*.7z",
        "*.tar",
        "*.tar.gz",
        "*.tgz",
        "*.tar.bz2",
        "*.tbz2",
        "*.tar.xz",
        "*.txz",
        # Ignore files themselves
        ".gitignore",
        ".folder2md_ignore",
        ".gptignore",
        # Config files that might contain secrets
        ".env",
        ".env.*",
        "*.key",
        "*.pem",
        "*.crt",
        "*.p12",
        "*.pfx",
        "secrets.yaml",
        "secrets.yml",
        "secrets.json",
    ]

    def __init__(
        self,
        patterns: list[str] | None = None,
        loaded_files: list[str] | None = None,
    ):
        """Initialize with custom patterns or defaults."""
        self.patterns = patterns or self.DEFAULT_PATTERNS.copy()
        self.loaded_files = loaded_files or []
        self.parsed_patterns = self._parse_patterns()
        self.compiled_patterns = self._compile_patterns()

    def _parse_patterns(self) -> list[tuple[str, bool, bool]]:
        """Parse patterns to extract pattern, negation, and directory flags.

        Returns:
            List of tuples: (pattern, is_negated, is_directory_only)
        """
        parsed = []

        for pattern in self.patterns:
            # Skip empty lines and comments
            pattern = pattern.strip()
            if not pattern or pattern.startswith("#"):
                continue

            # Check for negation
            is_negated = False
            if pattern.startswith("!"):
                is_negated = True
                pattern = pattern[1:].strip()

            # Check for directory-only pattern
            is_directory_only = False
            if pattern.endswith("/"):
                is_directory_only = True
                pattern = pattern[:-1]

            # Handle leading slash (absolute from repo root)
            if pattern.startswith("/"):
                pattern = pattern[1:]

            parsed.append((pattern, is_negated, is_directory_only))

        return parsed

    def _compile_patterns(self) -> list[re.Pattern]:
        """Compile glob patterns to regex for faster matching."""
        compiled = []
        for pattern in self.patterns:
            try:
                # Convert glob pattern to regex
                regex = fnmatch.translate(pattern)
                compiled.append(re.compile(regex))
            except re.error:
                # If regex compilation fails, skip this pattern
                continue
        return compiled

    def should_ignore(self, path: Path, base_path: Path) -> bool:
        """Check if a path should be ignored with gitignore-style negation support."""
        # Get relative path from base
        try:
            rel_path = path.relative_to(base_path)
        except ValueError:
            # Path is not relative to base_path
            return False

        # Convert to string with forward slashes (for consistency)
        path_str = str(rel_path).replace("\\", "/")
        is_directory = path.is_dir()

        # Process patterns in order, last match wins
        # This ensures higher priority files (target directory) override lower priority ones
        should_ignore = False

        for pattern, is_negated, is_directory_only in self.parsed_patterns:
            # Skip directory-only patterns for files
            if is_directory_only and not is_directory:
                continue

            if self._matches_gitignore_pattern(path_str, pattern, is_directory):
                should_ignore = not is_negated

        return should_ignore

    def _matches_gitignore_pattern(
        self, path_str: str, pattern: str, is_directory: bool
    ) -> bool:
        """Check if a path matches a gitignore-style pattern.

        Args:
            path_str: The path to check (relative, with forward slashes)
            pattern: The pattern to match against
            is_directory: Whether the path is a directory

        Returns:
            True if the path matches the pattern
        """
        # Handle special cases
        if not pattern:
            return False

        # Handle ** patterns (match any number of directories)
        if "**" in pattern:
            return self._matches_double_star_pattern(path_str, pattern)

        # Handle directory patterns
        if "/" in pattern:
            # Pattern contains slash, match against full path
            return fnmatch.fnmatch(path_str, pattern)
        else:
            # Pattern doesn't contain slash, match against basename or any path segment
            path_parts = path_str.split("/")

            # Check if pattern matches the basename
            if fnmatch.fnmatch(path_parts[-1], pattern):
                return True

            # Check if pattern matches any directory in the path
            for part in path_parts:
                if fnmatch.fnmatch(part, pattern):
                    return True

            return False

    def _matches_double_star_pattern(self, path_str: str, pattern: str) -> bool:
        """Handle ** patterns which match any number of directories."""
        # Convert ** to appropriate regex
        # ** matches zero or more directories
        regex_pattern = pattern.replace("**", ".*")
        regex_pattern = regex_pattern.replace("*", "[^/]*")  # Regular * doesn't match /

        try:
            return bool(re.match(regex_pattern, path_str))
        except re.error:
            return False

    def _matches_pattern(self, path_str: str, pattern: str) -> bool:
        """Check if a path matches a pattern."""
        # Handle different pattern types
        if pattern.endswith("/**/*"):
            # Directory and all contents
            dir_pattern = pattern[:-5]  # Remove '/**/*'
            if fnmatch.fnmatch(path_str, dir_pattern) or path_str.startswith(
                dir_pattern + "/"
            ):
                return True
        elif pattern.endswith("/*"):
            # Direct contents of directory
            dir_pattern = pattern[:-2]  # Remove '/*'
            if fnmatch.fnmatch(path_str, dir_pattern + "/*"):
                return True
        elif "**/" in pattern:
            # Recursive pattern
            return fnmatch.fnmatch(path_str, pattern)
        else:
            # Simple pattern
            return fnmatch.fnmatch(path_str, pattern)

        return False

    def add_pattern(self, pattern: str) -> None:
        """Add a new ignore pattern."""
        if pattern not in self.patterns:
            self.patterns.append(pattern)
            self.parsed_patterns = self._parse_patterns()
            self.compiled_patterns = self._compile_patterns()

    def remove_pattern(self, pattern: str) -> None:
        """Remove an ignore pattern."""
        if pattern in self.patterns:
            self.patterns.remove(pattern)
            self.parsed_patterns = self._parse_patterns()
            self.compiled_patterns = self._compile_patterns()

    @classmethod
    def from_file(cls, ignore_file: Path) -> "IgnorePatterns":
        """Create IgnorePatterns from a .folder2md_ignore file."""
        patterns = cls.DEFAULT_PATTERNS.copy()

        if ignore_file.exists():
            try:
                with open(ignore_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            patterns.append(line)
            except OSError:
                pass

        return cls(patterns, loaded_files=[str(ignore_file)])

    @classmethod
    def from_hierarchical_files(
        cls, target_dir: Path, cwd: Path | None = None
    ) -> "IgnorePatterns":
        """Load ignore patterns from hierarchical .folder2md_ignore files.

        Priority order (highest to lowest):
        1. target_dir/.folder2md_ignore (highest priority)
        2. cwd/.folder2md_ignore (medium priority)
        3. ~/.folder2md_ignore (lowest priority)

        Args:
            target_dir: Directory being analyzed
            cwd: Current working directory (defaults to Path.cwd())

        Returns:
            IgnorePatterns instance with combined patterns and file tracking
        """
        if cwd is None:
            cwd = Path.cwd()

        all_patterns = cls.DEFAULT_PATTERNS.copy()
        loaded_files = []

        # Load global ignore file (~/.folder2md_ignore)
        global_ignore = Path.home() / ".folder2md_ignore"
        if global_ignore.exists():
            try:
                with open(global_ignore, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            all_patterns.append(line)
                loaded_files.append(f"{global_ignore} (global)")
            except OSError:
                pass

        # Load cwd ignore file (if different from target)
        cwd_ignore = cwd / ".folder2md_ignore"
        if cwd_ignore.exists() and cwd_ignore != target_dir / ".folder2md_ignore":
            try:
                with open(cwd_ignore, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            all_patterns.append(line)
                loaded_files.append(f"{cwd_ignore} (current directory)")
            except OSError:
                pass

        # Load target directory ignore file (highest priority)
        target_ignore = target_dir / ".folder2md_ignore"
        if target_ignore.exists():
            try:
                with open(target_ignore, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            all_patterns.append(line)
                loaded_files.append(
                    f"{target_ignore} (target directory) [highest priority]"
                )
            except OSError:
                pass

        return cls(all_patterns, loaded_files=loaded_files)

    @classmethod
    def from_gitignore(
        cls, gitignore_file: Path, include_defaults: bool = True
    ) -> "IgnorePatterns":
        """Load ignore patterns from a .gitignore file.

        Args:
            gitignore_file: Path to .gitignore file
            include_defaults: Whether to include default patterns

        Returns:
            IgnorePatterns instance with gitignore patterns
        """
        patterns = []
        if gitignore_file.exists():
            try:
                with open(gitignore_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        # Include all lines for proper gitignore parsing
                        patterns.append(line)
            except (OSError, UnicodeDecodeError):
                # If file can't be read, use defaults
                pass

        # Optionally combine with defaults
        if include_defaults:
            all_patterns = cls.DEFAULT_PATTERNS.copy()
            all_patterns.extend(patterns)
            return cls(all_patterns)
        else:
            return cls(patterns)

    @classmethod
    def from_multiple_gitignores(
        cls, repo_path: Path, include_defaults: bool = True
    ) -> "IgnorePatterns":
        """Load ignore patterns from multiple .gitignore files in repository hierarchy.

        Args:
            repo_path: Path to repository root
            include_defaults: Whether to include default patterns

        Returns:
            IgnorePatterns instance with combined gitignore patterns
        """
        all_patterns = []

        if include_defaults:
            all_patterns.extend(cls.DEFAULT_PATTERNS)

        # Look for .gitignore files from repo root up to current directory
        current_path = repo_path
        while current_path.exists():
            gitignore_file = current_path / ".gitignore"
            if gitignore_file.exists():
                try:
                    with open(gitignore_file, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            # Include all lines for proper gitignore parsing
                            all_patterns.append(line)
                except (OSError, UnicodeDecodeError):
                    continue

            # Move to parent directory
            if current_path.parent == current_path:
                break
            current_path = current_path.parent

        return cls(all_patterns)

    def write_default_ignore_file(self, file_path: Path) -> None:
        """Write a default .folder2md_ignore file."""
        content = [
            "# folder2md4llms ignore file",
            "# This file specifies patterns for files and directories to ignore",
            "# when processing a repository.",
            "",
            "# Version control",
            ".git/",
            ".svn/",
            ".hg/",
            "",
            "# Build artifacts",
            "__pycache__/",
            "*.pyc",
            "build/",
            "dist/",
            "*.egg-info/",
            "node_modules/",
            "target/",
            "",
            "# IDE files",
            ".vscode/",
            ".idea/",
            "*.sublime-*",
            "",
            "# OS files",
            ".DS_Store",
            "Thumbs.db",
            "",
            "# Temporary files",
            "*.tmp",
            "*.log",
            "*~",
            "",
            "# Add your custom patterns below:",
            "",
        ]

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(content))
        except OSError:
            pass
