"""Tests for ignore suggestions functionality."""

from unittest.mock import Mock

from folder2md4llms.utils.ignore_suggestions import IgnoreSuggester


class TestIgnoreSuggester:
    """Test the IgnoreSuggester class."""

    def test_init(self):
        """Test initialization of IgnoreSuggester."""
        suggester = IgnoreSuggester()
        assert suggester.min_file_size == 100_000
        assert suggester.min_dir_size == 1_000_000
        assert suggester.ignore_patterns is None
        assert suggester.suggestions == {}

    def test_init_with_custom_thresholds(self):
        """Test initialization with custom thresholds."""
        suggester = IgnoreSuggester(min_file_size=50_000, min_dir_size=500_000)
        assert suggester.min_file_size == 50_000
        assert suggester.min_dir_size == 500_000

    def test_is_cache_like(self):
        """Test cache-like pattern detection."""
        suggester = IgnoreSuggester()

        # Test cache-like names
        assert suggester._is_cache_like("cache")
        assert suggester._is_cache_like(".cache")
        assert suggester._is_cache_like("__pycache__")
        assert suggester._is_cache_like("mypy_cache")
        assert suggester._is_cache_like(".pytest_cache")
        assert suggester._is_cache_like("coverage")

        # Test non-cache-like names
        assert not suggester._is_cache_like("src")
        assert not suggester._is_cache_like("main.py")
        assert not suggester._is_cache_like("README.md")

    def test_is_temp_like(self):
        """Test temporary file pattern detection."""
        suggester = IgnoreSuggester()

        # Test temp-like names
        assert suggester._is_temp_like("tmp")
        assert suggester._is_temp_like("temp")
        assert suggester._is_temp_like(".tmp")
        assert suggester._is_temp_like("scratch")
        assert suggester._is_temp_like("work")

        # Test non-temp-like names
        assert not suggester._is_temp_like("src")
        assert not suggester._is_temp_like("main.py")

    def test_is_backup_like(self):
        """Test backup file pattern detection."""
        suggester = IgnoreSuggester()

        # Test backup-like names
        assert suggester._is_backup_like("backup")
        assert suggester._is_backup_like("file.bak")
        assert suggester._is_backup_like("old_version")
        assert suggester._is_backup_like("file.orig")
        assert suggester._is_backup_like("file~")

        # Test non-backup-like names
        assert not suggester._is_backup_like("main.py")
        assert not suggester._is_backup_like("README.md")

    def test_format_size(self):
        """Test file size formatting."""
        suggester = IgnoreSuggester()

        assert suggester._format_size(500) == "500.0 B"
        assert suggester._format_size(1500) == "1.5 KB"
        assert suggester._format_size(1_500_000) == "1.4 MB"
        assert suggester._format_size(1_500_000_000) == "1.4 GB"

    def test_analyze_path_with_ignore_patterns(self, tmp_path):
        """Test analyze_path with ignore patterns."""
        # Create a mock ignore patterns object
        mock_ignore = Mock()
        mock_ignore.should_ignore.return_value = True

        suggester = IgnoreSuggester(ignore_patterns=mock_ignore)

        # Create a large file
        large_file = tmp_path / "large_file.txt"
        large_file.write_text("x" * 200_000)  # 200KB file

        # Should not analyze ignored files
        suggester.analyze_path(large_file, tmp_path)

        # Should have no suggestions since file is ignored
        assert len(suggester.suggestions) == 0

    def test_analyze_path_without_ignore_patterns(self, tmp_path):
        """Test analyze_path without ignore patterns."""
        suggester = IgnoreSuggester()

        # Create a large cache file
        cache_file = tmp_path / "cache_file.txt"
        cache_file.write_text("x" * 200_000)  # 200KB file

        # Should analyze files when no ignore patterns
        suggester.analyze_path(cache_file, tmp_path)

        # Should have suggestions
        assert len(suggester.suggestions) > 0

    def test_get_suggestions(self):
        """Test getting suggestions."""
        suggester = IgnoreSuggester()

        # Manually add some suggestions
        suggester.suggestions = {
            "cache_files": {"cache.txt", "temp.log"},
            "hidden_files": {".large_file"},
        }

        suggestions = suggester.get_suggestions()

        assert len(suggestions) == 2
        assert ("💾 Cache Files", ["cache.txt", "temp.log"]) in suggestions
        assert ("🔒 Large Hidden Files", [".large_file"]) in suggestions

    def test_display_suggestions(self, tmp_path, capsys):
        """Test displaying suggestions."""
        suggester = IgnoreSuggester()

        # Manually add some suggestions
        suggester.suggestions = {
            "cache_files": {"cache.txt"},
        }

        output_file = tmp_path / "output.md"
        suggester.display_suggestions(output_file)

        # Check that output was printed (captured by capsys)
        captured = capsys.readouterr()
        assert "Ignore Suggestions" in captured.out
        assert "cache.txt" in captured.out

    def test_no_suggestions_display(self, tmp_path, capsys):
        """Test display when no suggestions."""
        suggester = IgnoreSuggester()

        output_file = tmp_path / "output.md"
        suggester.display_suggestions(output_file)

        # Should not print anything when no suggestions
        captured = capsys.readouterr()
        assert "Ignore Suggestions" not in captured.out

    def test_is_binary_data_file(self):
        """Test binary data file detection."""
        suggester = IgnoreSuggester()

        # Test scientific data formats
        assert suggester._is_binary_data_file("structure.cif", ".cif")
        assert suggester._is_binary_data_file("data.h5", ".h5")
        assert suggester._is_binary_data_file("matrix.mat", ".mat")
        assert suggester._is_binary_data_file("array.npy", ".npy")
        assert suggester._is_binary_data_file("dataset.parquet", ".parquet")

        # Test non-binary data files
        assert not suggester._is_binary_data_file("code.py", ".py")
        assert not suggester._is_binary_data_file("config.json", ".json")

    def test_is_media_file(self):
        """Test media file detection."""
        suggester = IgnoreSuggester()

        # Test images
        assert suggester._is_media_file(".png")
        assert suggester._is_media_file(".jpg")
        assert suggester._is_media_file(".gif")

        # Test videos
        assert suggester._is_media_file(".mp4")
        assert suggester._is_media_file(".avi")

        # Test audio
        assert suggester._is_media_file(".mp3")
        assert suggester._is_media_file(".wav")

        # Test non-media files
        assert not suggester._is_media_file(".py")
        assert not suggester._is_media_file(".txt")

    def test_is_build_artifact(self):
        """Test build artifact detection."""
        suggester = IgnoreSuggester()

        # Test compiled files
        assert suggester._is_build_artifact("module.pyc", ".pyc")
        assert suggester._is_build_artifact("library.so", ".so")
        assert suggester._is_build_artifact("program.exe", ".exe")

        # Test minified files
        assert suggester._is_build_artifact("app.min.js", ".js")
        assert suggester._is_build_artifact("style.min.css", ".css")

        # Test non-build artifacts
        assert not suggester._is_build_artifact("source.py", ".py")
        assert not suggester._is_build_artifact("config.json", ".json")

    def test_large_file_threshold(self, tmp_path):
        """Test large file threshold detection."""
        suggester = IgnoreSuggester(large_file_threshold=1_000_000)  # 1MB

        # Create a file larger than threshold
        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * 1_500_000)  # 1.5MB

        suggester.analyze_path(large_file, tmp_path)

        suggestions = suggester.get_suggestions()
        assert len(suggestions) > 0
        assert any("Large Files" in category for category, _ in suggestions)

    def test_binary_data_file_suggestion(self, tmp_path):
        """Test that binary data files are suggested regardless of size."""
        suggester = IgnoreSuggester()

        # Create a small .cif file
        cif_file = tmp_path / "structure.cif"
        cif_file.write_text("small content")

        suggester.analyze_path(cif_file, tmp_path)

        suggestions = suggester.get_suggestions()
        assert len(suggestions) > 0
        # Should suggest *.cif pattern
        assert any("Binary Data Files" in category for category, _ in suggestions)
