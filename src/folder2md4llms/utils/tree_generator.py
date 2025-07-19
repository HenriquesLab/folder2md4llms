"""Tree structure generator for folder visualization."""

from pathlib import Path

from .ignore_patterns import IgnorePatterns


class TreeGenerator:
    """Generates ASCII tree representation of folder structure."""

    def __init__(self, ignore_patterns: IgnorePatterns):
        self.ignore_patterns = ignore_patterns
        self.tree_symbols = {
            "branch": "├── ",
            "last_branch": "└── ",
            "vertical": "│   ",
            "space": "    ",
        }

    def generate_tree(self, root_path: Path, max_depth: int = 10) -> str:
        """Generate ASCII tree representation of directory structure."""
        lines = [str(root_path.name) + "/"]

        try:
            self._generate_tree_recursive(
                root_path, lines, prefix="", depth=0, max_depth=max_depth
            )
        except OSError:
            lines.append("Error reading directory structure")

        return "\n".join(lines)

    def _generate_tree_recursive(
        self, path: Path, lines: list[str], prefix: str, depth: int, max_depth: int
    ) -> None:
        """Recursively generate tree structure."""
        if depth >= max_depth:
            return

        try:
            # Get all items in directory
            items = list(path.iterdir())

            # Filter ignored items
            filtered_items = []
            for item in items:
                if not self.ignore_patterns.should_ignore(item, path):
                    filtered_items.append(item)

            # Sort items: directories first, then files
            filtered_items.sort(key=lambda x: (x.is_file(), x.name.lower()))

            # Process each item
            for i, item in enumerate(filtered_items):
                is_last = i == len(filtered_items) - 1

                # Choose appropriate symbol
                if is_last:
                    symbol = self.tree_symbols["last_branch"]
                    next_prefix = prefix + self.tree_symbols["space"]
                else:
                    symbol = self.tree_symbols["branch"]
                    next_prefix = prefix + self.tree_symbols["vertical"]

                # Add item to tree
                if item.is_dir():
                    lines.append(f"{prefix}{symbol}{item.name}/")
                    # Recursively process subdirectory
                    self._generate_tree_recursive(
                        item, lines, next_prefix, depth + 1, max_depth
                    )
                else:
                    lines.append(f"{prefix}{symbol}{item.name}")

        except (OSError, PermissionError):
            lines.append(f"{prefix}[Error reading directory]")

    def generate_simple_tree(self, root_path: Path) -> str:
        """Generate a simple tree without symbols (for compatibility)."""
        lines = []

        def add_items(path: Path, indent: int = 0):
            prefix = "  " * indent
            try:
                items = list(path.iterdir())

                # Filter ignored items
                filtered_items = []
                for item in items:
                    if not self.ignore_patterns.should_ignore(item, root_path):
                        filtered_items.append(item)

                # Sort items
                filtered_items.sort(key=lambda x: (x.is_file(), x.name.lower()))

                for item in filtered_items:
                    if item.is_dir():
                        lines.append(f"{prefix}{item.name}/")
                        add_items(item, indent + 1)
                    else:
                        lines.append(f"{prefix}{item.name}")

            except (OSError, PermissionError):
                lines.append(f"{prefix}[Error reading directory]")

        lines.append(f"{root_path.name}/")
        add_items(root_path, 1)

        return "\n".join(lines)

    def count_items(self, root_path: Path) -> dict[str, object]:
        """Count files and directories in the tree."""
        counts: dict[str, object] = {
            "total_files": 0,
            "total_dirs": 0,
            "total_size": 0,
            "by_extension": {},
        }

        def count_recursive(path: Path):
            try:
                for item in path.iterdir():
                    if self.ignore_patterns.should_ignore(item, root_path):
                        continue

                    if item.is_dir():
                        total_dirs = counts["total_dirs"]
                        if isinstance(total_dirs, int):
                            counts["total_dirs"] = total_dirs + 1
                        count_recursive(item)
                    else:
                        total_files = counts["total_files"]
                        if isinstance(total_files, int):
                            counts["total_files"] = total_files + 1
                        try:
                            size = item.stat().st_size
                            total_size = counts["total_size"]
                            if isinstance(total_size, int):
                                counts["total_size"] = total_size + size

                            # Count by extension
                            ext = item.suffix.lower()
                            if ext:
                                by_ext = counts["by_extension"]
                                if isinstance(by_ext, dict):
                                    by_ext[ext] = by_ext.get(ext, 0) + 1
                        except OSError:
                            pass

            except (OSError, PermissionError):
                pass

        count_recursive(root_path)
        return counts
