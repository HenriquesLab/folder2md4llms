"""Ignore patterns handling for filtering files."""

import fnmatch
import re
from pathlib import Path
from typing import List, Optional


class IgnorePatterns:
    """Handles file and directory ignore patterns."""

    DEFAULT_PATTERNS = [
        # Version control
        ".git/*",
        ".git/**/*",
        ".svn/*",
        ".svn/**/*",
        ".hg/*",
        ".hg/**/*",
        ".bzr/*",
        ".bzr/**/*",
        # Build artifacts
        "__pycache__/*",
        "__pycache__/**/*",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".Python",
        "build/*",
        "build/**/*",
        "dist/*",
        "dist/**/*",
        "*.egg-info/*",
        "*.egg-info/**/*",
        ".eggs/*",
        ".eggs/**/*",
        # Dependencies
        "node_modules/*",
        "node_modules/**/*",
        "venv/*",
        "venv/**/*",
        "env/*",
        "env/**/*",
        ".venv/*",
        ".venv/**/*",
        "virtualenv/*",
        "virtualenv/**/*",
        "target/*",
        "target/**/*",
        "vendor/*",
        "vendor/**/*",
        # IDE files
        ".vscode/*",
        ".vscode/**/*",
        ".idea/*",
        ".idea/**/*",
        "*.sublime-*",
        ".atom/*",
        ".atom/**/*",
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
        "logs/*",
        "logs/**/*",
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

    def __init__(self, patterns: Optional[List[str]] = None):
        """Initialize with custom patterns or defaults."""
        self.patterns = patterns or self.DEFAULT_PATTERNS.copy()
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> List[re.Pattern]:
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
        """Check if a path should be ignored."""
        # Get relative path from base
        try:
            rel_path = path.relative_to(base_path)
        except ValueError:
            # Path is not relative to base_path
            return False

        # Convert to string with forward slashes (for consistency)
        path_str = str(rel_path).replace("\\", "/")

        # Check against all patterns
        for pattern in self.patterns:
            if self._matches_pattern(path_str, pattern):
                return True

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
            self.compiled_patterns = self._compile_patterns()

    def remove_pattern(self, pattern: str) -> None:
        """Remove an ignore pattern."""
        if pattern in self.patterns:
            self.patterns.remove(pattern)
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

        return cls(patterns)

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
