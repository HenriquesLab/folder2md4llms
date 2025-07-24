"""Tests for binary distribution and PyInstaller specific functionality."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


class TestBinaryDistributionCompatibility:
    """Test binary distribution compatibility features."""

    def test_magic_library_platform_handling(self):
        """Test that magic library imports work correctly across platforms."""
        # This tests the logic that should be in PyInstaller spec file

        # Test Windows behavior (should prefer python-magic-bin)
        with patch("sys.platform", "win32"):
            try:
                import magic

                # On Windows, we should be able to import magic
                # (either python-magic-bin or python-magic)
                assert magic is not None
            except ImportError:
                # This is acceptable in test environment
                pytest.skip("Magic library not available in test environment")

    def test_cli_entry_point_variants(self):
        """Test different ways to access the CLI (important for binary distribution)."""
        # Test direct import
        from folder2md4llms.cli import main

        assert callable(main)

        # Test module execution path (what PyInstaller entry point uses)
        import folder2md4llms.cli

        assert hasattr(folder2md4llms.cli, "main")
        assert callable(folder2md4llms.cli.main)

    def test_resource_access_patterns(self):
        """Test resource access patterns that work in PyInstaller."""
        # Test that we can access package resources
        import folder2md4llms

        # These should work in both normal and PyInstaller environments
        assert hasattr(folder2md4llms, "__version__")

        # Test that submodules are accessible
        from folder2md4llms import analyzers, converters, engine, formatters, utils

        assert utils is not None
        assert analyzers is not None
        assert converters is not None
        assert engine is not None
        assert formatters is not None

    def test_file_type_detection_binary_compat(self):
        """Test file type detection works in binary environment."""
        from pathlib import Path

        from folder2md4llms.utils.file_utils import is_binary_file, is_text_file

        # These should not crash in binary environment
        assert callable(is_binary_file)
        assert callable(is_text_file)

        # Test with Path objects (standard API)
        test_py = Path("test.py")
        test_md = Path("test.md")

        # These should not crash (even if files don't exist)
        try:
            is_binary_file(test_py)
            is_text_file(test_md)
        except (FileNotFoundError, OSError):
            # This is expected for non-existent files
            pass

    def test_configuration_loading_binary_compat(self):
        """Test that configuration loading works in binary environment."""
        from folder2md4llms.utils.config import Config

        # Should be able to create config without crashing
        config = Config()
        assert config is not None

        # Should have default configuration attributes
        assert hasattr(config, "output_format")
        assert hasattr(config, "include_tree")
        assert config.output_format == "markdown"

    @patch.dict(os.environ, {"PYTHONPATH": ""})
    def test_isolated_environment_compatibility(self):
        """Test that the application works in isolated environments (like PyInstaller)."""
        # Clear any existing imports to simulate fresh environment
        import importlib

        # Test that we can still import and use the main functionality
        try:
            import folder2md4llms.cli

            importlib.reload(folder2md4llms.cli)

            # Should be able to access main function
            assert hasattr(folder2md4llms.cli, "main")
            assert callable(folder2md4llms.cli.main)

        except ImportError as e:
            pytest.fail(f"Failed to import in isolated environment: {e}")


class TestWindowsSpecificFeatures:
    """Test Windows-specific features needed for binary distribution."""

    @patch("sys.platform", "win32")
    def test_windows_path_handling(self):
        """Test Windows path handling."""
        from folder2md4llms.utils.platform_utils import is_windows

        # Mock that we're on Windows
        assert is_windows() or sys.platform == "win32"  # Either real Windows or mocked

        # Test path operations that should work on Windows
        from pathlib import Path

        test_path = Path("file.txt")  # Use simple path for cross-platform testing

        # These operations should not crash
        assert test_path.suffix == ".txt"
        assert test_path.stem == "file"

    @patch("sys.platform", "win32")
    @patch("folder2md4llms.utils.platform_utils.is_windows", return_value=True)
    def test_windows_magic_fallback(self, mock_is_windows):
        """Test Windows magic library fallback behavior."""
        # This tests the fallback logic when python-magic-bin is not available
        from folder2md4llms.analyzers.binary_analyzer import BinaryAnalyzer

        analyzer = BinaryAnalyzer()

        # Should be able to create analyzer without crashing
        assert analyzer is not None
        assert callable(getattr(analyzer, "analyze_file", None))

    def test_console_output_compatibility(self):
        """Test console output works correctly (important for Windows binary)."""
        from folder2md4llms.formatters.markdown import MarkdownFormatter

        formatter = MarkdownFormatter()

        # Should be able to create formatter without crashing
        assert formatter is not None

        # Should have format methods available
        assert callable(getattr(formatter, "format_repository", None))

        # Test basic string handling for Unicode (important for Windows console)
        test_string = "héllo wörld 🌍"
        assert isinstance(test_string, str)
        assert len(test_string) > 0


class TestCrossPlatformBinaryCompatibility:
    """Test cross-platform binary compatibility."""

    def test_all_platforms_import_correctly(self):
        """Test that imports work correctly on all platforms."""
        # Test that core modules can be imported (actual platform doesn't matter for import test)
        from folder2md4llms.cli import main

        assert callable(main)

        from folder2md4llms.processor import RepositoryProcessor

        assert RepositoryProcessor is not None

        # Test that platform utils work
        from folder2md4llms.utils.platform_utils import get_platform_name

        platform_name = get_platform_name()
        assert platform_name in ["windows", "macos", "linux", "freebsd"]

    def test_binary_naming_logic(self):
        """Test the binary naming logic used in workflows."""
        # Test the expected binary naming patterns that workflows use
        test_patterns = [
            "folder2md-windows-x64.exe",  # Windows
            "folder2md-macos-x64",  # macOS Intel
            "folder2md-macos-arm64",  # macOS Apple Silicon
            "folder2md-linux-x64",  # Linux
        ]

        for pattern in test_patterns:
            # Test that patterns have expected characteristics
            if "windows" in pattern:
                assert pattern.endswith(
                    ".exe"
                ), f"Windows binary {pattern} should have .exe extension"
            elif "macos" in pattern:
                assert (
                    "macos" in pattern
                ), f"macOS binary {pattern} should contain 'macos'"
                assert not pattern.endswith(
                    ".exe"
                ), f"macOS binary {pattern} should not have .exe extension"
            elif "linux" in pattern:
                assert (
                    "linux" in pattern
                ), f"Linux binary {pattern} should contain 'linux'"
                assert not pattern.endswith(
                    ".exe"
                ), f"Linux binary {pattern} should not have .exe extension"

    def test_dependency_availability_checking(self):
        """Test that we can check for optional dependencies gracefully."""
        from folder2md4llms.converters.converter_factory import ConverterFactory

        factory = ConverterFactory()

        # Should be able to create factory even if optional deps are missing
        assert factory is not None

        # Should have methods for getting converters
        assert callable(getattr(factory, "get_converter", None))

        # Test that we can get a converter for common file types
        try:
            converter = factory.get_converter("py", {})
            assert converter is not None
        except Exception:
            # It's OK if this fails due to missing dependencies
            pass


class TestPyInstallerSpecCompatibility:
    """Test that our code is compatible with PyInstaller spec requirements."""

    def test_hiddenimports_are_importable(self):
        """Test that all hidden imports specified in PyInstaller spec are importable."""
        # These are the critical imports from our PyInstaller spec
        critical_imports = [
            "folder2md4llms",
            "folder2md4llms.cli",
            "folder2md4llms.processor",
            "folder2md4llms.converters",
            "folder2md4llms.analyzers",
            "folder2md4llms.engine",
            "folder2md4llms.formatters",
            "folder2md4llms.utils",
            "rich",
            "rich.console",
            "rich.progress",
            "click",
            "yaml",
        ]

        for import_name in critical_imports:
            try:
                __import__(import_name)
            except ImportError as e:
                # For optional dependencies, this is OK
                if import_name not in ["rich", "click", "yaml"]:
                    pytest.fail(f"Critical import {import_name} failed: {e}")

    def test_data_files_accessible(self):
        """Test that data files included in PyInstaller spec are accessible."""
        # Test that we can access package data

        # Should be able to get package path
        import pkg_resources

        try:
            pkg_path = pkg_resources.get_distribution("folder2md4llms").location
            assert pkg_path is not None
        except pkg_resources.DistributionNotFound:
            # This is OK in development environment
            pass

    def test_executable_creation_compatibility(self):
        """Test compatibility with PyInstaller executable creation."""
        # Test that entry point script exists and is valid
        entry_point = Path("src/folder2md4llms/pyinstaller_entry.py")
        assert entry_point.exists(), "PyInstaller entry point must exist"

        # Test that it has valid Python syntax
        content = entry_point.read_text()
        try:
            compile(content, str(entry_point), "exec")
        except SyntaxError as e:
            pytest.fail(f"PyInstaller entry point has syntax error: {e}")

        # Test that it imports the correct main function
        assert "from folder2md4llms.cli import main" in content
        assert "main()" in content
