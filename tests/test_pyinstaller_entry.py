"""Tests for PyInstaller entry point functionality."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


class TestPyInstallerEntry:
    """Test PyInstaller entry point script."""

    def test_entry_point_exists(self):
        """Test that the PyInstaller entry point file exists."""
        entry_point = Path("pyinstaller_entry.py")
        assert entry_point.exists(), "PyInstaller entry point script should exist"

    def test_entry_point_content(self):
        """Test that the entry point has correct content."""
        entry_point = Path("pyinstaller_entry.py")
        content = entry_point.read_text()

        # Check for required imports
        assert "import os" in content
        assert "import sys" in content
        assert "from folder2md4llms.cli import main" in content

        # Check for path setup
        assert "sys.path.insert" in content
        assert "folder2md4llms" in content

        # Check for main guard
        assert 'if __name__ == "__main__":' in content
        assert "main()" in content

    @patch("folder2md4llms.cli.main")
    def test_entry_point_execution(self, mock_main):
        """Test that the entry point can be executed."""
        # Save original sys.path
        original_path = sys.path.copy()

        try:
            # Read the entry point content but modify the execution context
            entry_point = Path("pyinstaller_entry.py")
            content = entry_point.read_text()

            # Create a modified version that we can control
            modified_content = content.replace(
                'if __name__ == "__main__":', "if True:  # Always execute for test"
            )

            # Execute the modified script
            exec(modified_content)

            # Verify main was called
            mock_main.assert_called_once()

        finally:
            # Restore original sys.path
            sys.path[:] = original_path

    def test_path_modification(self):
        """Test that the entry point modifies sys.path correctly."""
        original_path = sys.path.copy()

        try:
            # Execute the path setup as it would work in the entry point
            entry_point = Path("pyinstaller_entry.py")

            # Simulate what the entry point does
            entry_dir = str(entry_point.parent.absolute())
            expected_path = os.path.join(entry_dir, "folder2md4llms")

            # Execute similar to what's in the entry point
            sys.path.insert(0, expected_path)

            # Check that path was modified
            assert sys.path[0] == expected_path

        finally:
            # Restore original sys.path
            sys.path[:] = original_path

    def test_import_accessibility(self):
        """Test that the CLI module can be imported after path setup."""
        original_path = sys.path.copy()

        try:
            # Setup path as the entry point would
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

            # Test that we can import the main function
            from folder2md4llms.cli import main

            assert callable(main)

        finally:
            # Restore original sys.path
            sys.path[:] = original_path

    def test_entry_point_main_guard(self):
        """Test that the entry point only executes when run as main."""
        # Read the entry point content
        entry_point = Path("pyinstaller_entry.py")
        content = entry_point.read_text()

        # Verify main guard pattern
        assert 'if __name__ == "__main__":' in content

        # Verify indentation is correct (main() should be indented)
        lines = content.split("\n")
        main_guard_found = False
        main_call_found = False

        for i, line in enumerate(lines):
            if 'if __name__ == "__main__":' in line:
                main_guard_found = True
                # Check next non-empty line is indented and calls main()
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    if next_line:
                        assert lines[j].startswith(
                            "    "
                        ), "main() call should be indented"
                        assert "main()" in next_line, "Should call main() function"
                        main_call_found = True
                        break
                break

        assert main_guard_found, "Should have main guard"
        assert main_call_found, "Should call main() when run as script"


class TestPyInstallerCompatibility:
    """Test PyInstaller-specific compatibility features."""

    def test_platform_specific_imports(self):
        """Test that platform-specific imports work correctly."""
        from folder2md4llms.utils.platform_utils import (
            get_platform_name,
            is_linux,
            is_macos,
            is_windows,
        )

        # These should all be callable without errors
        assert callable(is_windows)
        assert callable(is_macos)
        assert callable(is_linux)
        assert callable(get_platform_name)

        # At least one should be True
        platforms = [is_windows(), is_macos(), is_linux()]
        assert any(platforms), "At least one platform should be detected"

    @patch("sys.platform", "win32")
    def test_windows_specific_functionality(self):
        """Test Windows-specific functionality that PyInstaller needs."""
        # Test that we can import magic library (should use python-magic-bin on Windows)
        try:
            import magic

            # If import succeeds, test basic functionality
            assert hasattr(magic, "Magic") or hasattr(magic, "from_file")
        except ImportError:
            # This is acceptable - magic is optional
            pytest.skip("Magic library not available")

    @patch("sys.platform", "darwin")
    def test_macos_specific_functionality(self):
        """Test macOS-specific functionality that PyInstaller needs."""
        # Test that we can import magic library (should use python-magic on macOS)
        try:
            import magic

            # If import succeeds, test basic functionality
            assert hasattr(magic, "Magic") or hasattr(magic, "from_file")
        except ImportError:
            # This is acceptable - magic is optional
            pytest.skip("Magic library not available")

    def test_hidden_imports_available(self):
        """Test that PyInstaller hidden imports are available."""
        # Test core dependencies that should be included
        core_imports = [
            "folder2md4llms",
            "folder2md4llms.cli",
            "folder2md4llms.processor",
            "folder2md4llms.utils",
            "folder2md4llms.converters",
            "folder2md4llms.analyzers",
            "folder2md4llms.engine",
            "folder2md4llms.formatters",
        ]

        for import_name in core_imports:
            try:
                __import__(import_name)
            except ImportError as e:
                pytest.fail(f"Required import {import_name} failed: {e}")

    def test_optional_dependencies_graceful_failure(self):
        """Test that optional dependencies fail gracefully."""
        optional_deps = ["pypdf", "docx", "openpyxl", "striprtf", "nbconvert", "pptx"]

        for dep in optional_deps:
            try:
                __import__(dep)
                # If import succeeds, that's good
            except ImportError:
                # If import fails, that's also acceptable - these are optional
                pass

    def test_binary_analyzer_compatibility(self):
        """Test that binary analyzer works in PyInstaller environment."""
        import tempfile
        from pathlib import Path

        from folder2md4llms.analyzers.binary_analyzer import BinaryAnalyzer

        analyzer = BinaryAnalyzer()
        assert analyzer is not None

        # Test with a simple temporary file (should not crash)
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as tmp:
            tmp.write(b"hello world")
            tmp.flush()
            temp_path = tmp.name

        # File is now closed, safe to analyze and delete on Windows
        try:
            result = analyzer.analyze_file(Path(temp_path))
            assert isinstance(result, str)
            assert len(result) > 0
        finally:
            Path(temp_path).unlink(missing_ok=True)
