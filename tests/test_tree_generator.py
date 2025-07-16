"""Tests for tree structure generation."""

from folder2md4llms.utils.ignore_patterns import IgnorePatterns
from folder2md4llms.utils.tree_generator import TreeGenerator


class TestTreeGenerator:
    """Test the TreeGenerator class."""

    def test_generate_tree_simple(self, sample_repo):
        """Test generating tree for simple repository."""
        patterns = IgnorePatterns([])  # No ignore patterns
        generator = TreeGenerator(patterns)

        tree = generator.generate_tree(sample_repo)

        assert "sample_repo/" in tree
        assert "README.md" in tree
        assert "main.py" in tree
        assert "src/" in tree
        assert "tests/" in tree
        assert "├──" in tree or "└──" in tree

    def test_generate_tree_with_ignore_patterns(self, sample_repo):
        """Test generating tree with ignore patterns."""
        patterns = IgnorePatterns(["*.py", "tests/*"])
        generator = TreeGenerator(patterns)

        tree = generator.generate_tree(sample_repo)

        assert "sample_repo/" in tree
        assert "README.md" in tree
        assert "main.py" not in tree
        assert "src/" in tree
        assert "test_module.py" not in tree

    def test_generate_tree_max_depth(self, sample_repo):
        """Test generating tree with depth limit."""
        patterns = IgnorePatterns([])
        generator = TreeGenerator(patterns)

        tree = generator.generate_tree(sample_repo, max_depth=1)

        assert "sample_repo/" in tree
        assert "src/" in tree
        assert "tests/" in tree
        # Should not show files inside subdirectories
        assert "module.py" not in tree

    def test_generate_simple_tree(self, sample_repo):
        """Test generating simple tree without symbols."""
        patterns = IgnorePatterns([])
        generator = TreeGenerator(patterns)

        tree = generator.generate_simple_tree(sample_repo)

        assert "sample_repo/" in tree
        assert "README.md" in tree
        assert "main.py" in tree
        assert "src/" in tree
        # Should use simple indentation
        assert "├──" not in tree
        assert "└──" not in tree

    def test_count_items(self, sample_repo):
        """Test counting items in the tree."""
        patterns = IgnorePatterns([])
        generator = TreeGenerator(patterns)

        counts = generator.count_items(sample_repo)

        assert counts["total_files"] > 0
        assert counts["total_dirs"] > 0
        assert counts["total_size"] > 0
        assert ".py" in counts["by_extension"]
        assert ".md" in counts["by_extension"]

    def test_count_items_with_ignore_patterns(self, sample_repo):
        """Test counting items with ignore patterns."""
        patterns = IgnorePatterns(["*.py"])
        generator = TreeGenerator(patterns)

        counts = generator.count_items(sample_repo)

        assert counts["total_files"] > 0
        assert ".py" not in counts["by_extension"]
        assert ".md" in counts["by_extension"]

    def test_empty_directory(self, temp_dir):
        """Test generating tree for empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        patterns = IgnorePatterns([])
        generator = TreeGenerator(patterns)

        tree = generator.generate_tree(empty_dir)

        assert "empty/" in tree
        assert len(tree.split("\n")) == 1  # Only the root directory

    def test_nested_directories(self, temp_dir):
        """Test generating tree for nested directories."""
        nested_path = temp_dir / "a" / "b" / "c"
        nested_path.mkdir(parents=True)
        (nested_path / "deep_file.txt").touch()

        patterns = IgnorePatterns([])
        generator = TreeGenerator(patterns)

        tree = generator.generate_tree(temp_dir)

        assert "a/" in tree
        assert "b/" in tree
        assert "c/" in tree
        assert "deep_file.txt" in tree

    def test_mixed_files_and_directories(self, temp_dir):
        """Test tree generation with mixed files and directories."""
        # Create mixed structure
        (temp_dir / "file1.txt").touch()
        (temp_dir / "dir1").mkdir()
        (temp_dir / "file2.txt").touch()
        (temp_dir / "dir2").mkdir()
        (temp_dir / "dir1" / "subfile.txt").touch()

        patterns = IgnorePatterns([])
        generator = TreeGenerator(patterns)

        tree = generator.generate_tree(temp_dir)

        # Should show directories first, then files (sorted)
        lines = tree.split("\n")
        assert any("dir1/" in line for line in lines)
        assert any("dir2/" in line for line in lines)
        assert any("file1.txt" in line for line in lines)
        assert any("file2.txt" in line for line in lines)
        assert any("subfile.txt" in line for line in lines)
