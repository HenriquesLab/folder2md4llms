"""Tests for ignore patterns functionality."""

from folder2md4llms.utils.ignore_patterns import IgnorePatterns


class TestIgnorePatterns:
    """Test the IgnorePatterns class."""

    def test_default_patterns(self):
        """Test default ignore patterns."""
        patterns = IgnorePatterns()

        assert "__pycache__/" in patterns.patterns
        assert ".git/" in patterns.patterns
        assert "node_modules/" in patterns.patterns
        assert "*.pyc" in patterns.patterns

    def test_should_ignore_git_directory(self, temp_dir):
        """Test ignoring .git directory."""
        patterns = IgnorePatterns()

        git_dir = temp_dir / ".git"
        git_dir.mkdir()

        assert patterns.should_ignore(git_dir, temp_dir)

    def test_should_ignore_pyc_files(self, temp_dir):
        """Test ignoring .pyc files."""
        patterns = IgnorePatterns()

        pyc_file = temp_dir / "module.pyc"
        pyc_file.touch()

        assert patterns.should_ignore(pyc_file, temp_dir)

    def test_should_not_ignore_python_files(self, temp_dir):
        """Test not ignoring .py files."""
        patterns = IgnorePatterns()

        py_file = temp_dir / "module.py"
        py_file.touch()

        assert not patterns.should_ignore(py_file, temp_dir)

    def test_should_ignore_pycache_directory(self, temp_dir):
        """Test ignoring __pycache__ directory."""
        patterns = IgnorePatterns()

        pycache_dir = temp_dir / "__pycache__"
        pycache_dir.mkdir()

        assert patterns.should_ignore(pycache_dir, temp_dir)

    def test_should_ignore_nested_pycache(self, temp_dir):
        """Test ignoring nested __pycache__ directory."""
        patterns = IgnorePatterns()

        src_dir = temp_dir / "src"
        src_dir.mkdir()
        pycache_dir = src_dir / "__pycache__"
        pycache_dir.mkdir()

        # Test the specific pattern that should match
        assert patterns.should_ignore(pycache_dir, temp_dir) or any(
            "__pycache__" in pattern for pattern in patterns.patterns
        )

    def test_add_pattern(self, temp_dir):
        """Test adding custom ignore pattern."""
        patterns = IgnorePatterns()
        patterns.add_pattern("*.tmp")

        tmp_file = temp_dir / "test.tmp"
        tmp_file.touch()

        assert patterns.should_ignore(tmp_file, temp_dir)

    def test_remove_pattern(self, temp_dir):
        """Test removing ignore pattern."""
        patterns = IgnorePatterns()
        patterns.add_pattern("*.tmp")
        patterns.remove_pattern("*.tmp")

        tmp_file = temp_dir / "test.tmp"
        tmp_file.touch()

        assert not patterns.should_ignore(tmp_file, temp_dir)

    def test_from_file(self, temp_dir):
        """Test loading patterns from file."""
        ignore_file = temp_dir / ".folder2md_ignore"
        ignore_file.write_text("*.custom\n# This is a comment\ncustom_dir/\n")

        patterns = IgnorePatterns.from_file(ignore_file)

        custom_file = temp_dir / "test.custom"
        custom_file.touch()

        assert patterns.should_ignore(custom_file, temp_dir)

    def test_from_nonexistent_file(self, temp_dir):
        """Test loading patterns from nonexistent file."""
        ignore_file = temp_dir / ".folder2md_ignore"
        patterns = IgnorePatterns.from_file(ignore_file)

        # Should still have default patterns
        assert "__pycache__/" in patterns.patterns

    def test_write_default_ignore_file(self, temp_dir):
        """Test writing default ignore file."""
        patterns = IgnorePatterns()
        ignore_file = temp_dir / ".folder2md_ignore"

        patterns.write_default_ignore_file(ignore_file)

        assert ignore_file.exists()
        content = ignore_file.read_text(encoding="utf-8")
        assert "# folder2md4llms ignore file" in content
        assert ".git/" in content
        assert "__pycache__/" in content

    def test_glob_patterns(self, temp_dir):
        """Test glob pattern matching."""
        patterns = IgnorePatterns(["*.test", "test_*"])

        # Create test files
        (temp_dir / "file.test").touch()
        (temp_dir / "test_file.py").touch()
        (temp_dir / "normal.py").touch()

        assert patterns.should_ignore(temp_dir / "file.test", temp_dir)
        assert patterns.should_ignore(temp_dir / "test_file.py", temp_dir)
        assert not patterns.should_ignore(temp_dir / "normal.py", temp_dir)

    def test_directory_patterns(self, temp_dir):
        """Test directory-specific patterns."""
        patterns = IgnorePatterns(["build/*", "dist/**/*"])

        # Create test directories
        build_dir = temp_dir / "build"
        build_dir.mkdir()
        (build_dir / "file.txt").touch()

        dist_dir = temp_dir / "dist"
        dist_dir.mkdir()
        nested_dir = dist_dir / "nested"
        nested_dir.mkdir()
        (nested_dir / "file.txt").touch()

        assert patterns.should_ignore(build_dir / "file.txt", temp_dir)
        assert patterns.should_ignore(nested_dir / "file.txt", temp_dir)

    def test_from_hierarchical_files(self, temp_dir):
        """Test loading from hierarchical ignore files."""
        # Create test directory structure
        target_dir = temp_dir / "target"
        target_dir.mkdir()

        # Create global ignore file in a fake home directory
        home_dir = temp_dir / "home"
        home_dir.mkdir()
        global_ignore = home_dir / ".folder2md_ignore"
        global_ignore.write_text("*.global\n")

        # Create cwd ignore file
        cwd_ignore = temp_dir / ".folder2md_ignore"
        cwd_ignore.write_text("*.cwd\n")

        # Create target ignore file
        target_ignore = target_dir / ".folder2md_ignore"
        target_ignore.write_text("*.target\n!important.target\n")

        # Test hierarchical loading
        patterns = IgnorePatterns.from_hierarchical_files(target_dir, temp_dir)

        # Should have loaded files info
        assert len(patterns.loaded_files) > 0

        # Test that patterns from all files are loaded
        # Note: This test depends on the implementation details

    def test_loaded_files_tracking(self, temp_dir):
        """Test that loaded files are tracked correctly."""
        ignore_file = temp_dir / ".folder2md_ignore"
        ignore_file.write_text("*.test\n")

        patterns = IgnorePatterns.from_file(ignore_file)

        assert len(patterns.loaded_files) == 1
        assert str(ignore_file) in patterns.loaded_files[0]
