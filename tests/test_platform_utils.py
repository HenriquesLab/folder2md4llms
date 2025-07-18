"""Comprehensive tests for platform-specific utilities."""

import platform
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from folder2md4llms.utils.platform_utils import (
    get_config_directory,
    get_default_shell,
    get_executable_extensions,
    get_library_search_paths,
    get_line_ending,
    get_magic_library_name,
    get_path_separator,
    get_platform_name,
    get_python_info,
    get_temp_directory,
    is_case_sensitive_filesystem,
    is_linux,
    is_macos,
    is_windows,
    normalize_path,
    supports_symlinks,
)


class TestPlatformDetection:
    """Test platform detection functions."""

    def test_platform_detection_consistency(self):
        """Test that platform detection is consistent."""
        # Only one of these should be true
        platforms = [is_windows(), is_macos(), is_linux()]
        assert sum(platforms) <= 1, "Multiple platforms detected as true"

    def test_get_platform_name(self):
        """Test getting platform name."""
        name = get_platform_name()
        assert isinstance(name, str)
        assert len(name) > 0
        assert (
            name in ["windows", "macos", "linux"] or name == platform.system().lower()
        )

    @patch("folder2md4llms.utils.platform_utils._platform_system", "windows")
    def test_is_windows_mocked(self):
        """Test Windows detection with mocked platform."""
        # Need to reload the module for the mock to take effect

        from folder2md4llms.utils import platform_utils

        # Patch the cached value
        platform_utils._platform_system = "windows"

        assert platform_utils.is_windows() is True
        assert platform_utils.is_macos() is False
        assert platform_utils.is_linux() is False
        assert platform_utils.get_platform_name() == "windows"

    @patch("folder2md4llms.utils.platform_utils._platform_system", "darwin")
    def test_is_macos_mocked(self):
        """Test macOS detection with mocked platform."""
        from folder2md4llms.utils import platform_utils

        # Patch the cached value
        platform_utils._platform_system = "darwin"

        assert platform_utils.is_windows() is False
        assert platform_utils.is_macos() is True
        assert platform_utils.is_linux() is False
        assert platform_utils.get_platform_name() == "macos"

    @patch("folder2md4llms.utils.platform_utils._platform_system", "linux")
    def test_is_linux_mocked(self):
        """Test Linux detection with mocked platform."""
        from folder2md4llms.utils import platform_utils

        # Patch the cached value
        platform_utils._platform_system = "linux"

        assert platform_utils.is_windows() is False
        assert platform_utils.is_macos() is False
        assert platform_utils.is_linux() is True
        assert platform_utils.get_platform_name() == "linux"

    @patch("folder2md4llms.utils.platform_utils._platform_system", "freebsd")
    def test_unknown_platform(self):
        """Test unknown platform handling."""
        from folder2md4llms.utils import platform_utils

        # Patch the cached value
        platform_utils._platform_system = "freebsd"

        assert platform_utils.is_windows() is False
        assert platform_utils.is_macos() is False
        assert platform_utils.is_linux() is False
        assert platform_utils.get_platform_name() == "freebsd"


class TestExecutableExtensions:
    """Test executable extension detection."""

    def test_get_executable_extensions(self):
        """Test getting executable extensions."""
        extensions = get_executable_extensions()
        assert isinstance(extensions, set)
        assert len(extensions) > 0
        assert all(ext.startswith(".") for ext in extensions)

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    def test_windows_executable_extensions(self, mock_is_windows):
        """Test Windows executable extensions."""
        mock_is_windows.return_value = True

        extensions = get_executable_extensions()
        expected = {".exe", ".bat", ".cmd", ".com", ".msi", ".dll"}
        assert extensions == expected

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    @patch("folder2md4llms.utils.platform_utils.is_macos")
    def test_macos_executable_extensions(self, mock_is_macos, mock_is_windows):
        """Test macOS executable extensions."""
        mock_is_windows.return_value = False
        mock_is_macos.return_value = True

        extensions = get_executable_extensions()
        expected = {".app", ".dmg", ".pkg", ".dylib"}
        assert extensions == expected

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    @patch("folder2md4llms.utils.platform_utils.is_macos")
    def test_linux_executable_extensions(self, mock_is_macos, mock_is_windows):
        """Test Linux executable extensions."""
        mock_is_windows.return_value = False
        mock_is_macos.return_value = False

        extensions = get_executable_extensions()
        expected = {".so", ".deb", ".rpm", ".AppImage", ".bin", ".run"}
        assert extensions == expected


class TestDirectoryPaths:
    """Test directory path functions."""

    def test_get_temp_directory(self):
        """Test getting temporary directory."""
        temp_dir = get_temp_directory()
        assert isinstance(temp_dir, Path)
        assert temp_dir.exists()
        assert temp_dir.is_dir()

        # Should be same as tempfile.gettempdir()
        expected = Path(tempfile.gettempdir())
        assert temp_dir == expected

    def test_get_config_directory(self):
        """Test getting configuration directory."""
        config_dir = get_config_directory()
        assert isinstance(config_dir, Path)
        assert "folder2md4llms" in str(config_dir)

        # Should be under home directory
        assert str(config_dir).startswith(str(Path.home()))

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    def test_windows_config_directory(self, mock_is_windows):
        """Test Windows configuration directory."""
        mock_is_windows.return_value = True

        config_dir = get_config_directory()
        expected = Path.home() / "AppData" / "Roaming" / "folder2md4llms"
        assert config_dir == expected

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    @patch("folder2md4llms.utils.platform_utils.is_macos")
    def test_macos_config_directory(self, mock_is_macos, mock_is_windows):
        """Test macOS configuration directory."""
        mock_is_windows.return_value = False
        mock_is_macos.return_value = True

        config_dir = get_config_directory()
        expected = Path.home() / "Library" / "Application Support" / "folder2md4llms"
        assert config_dir == expected

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    @patch("folder2md4llms.utils.platform_utils.is_macos")
    def test_linux_config_directory(self, mock_is_macos, mock_is_windows):
        """Test Linux configuration directory."""
        mock_is_windows.return_value = False
        mock_is_macos.return_value = False

        config_dir = get_config_directory()
        expected = Path.home() / ".config" / "folder2md4llms"
        assert config_dir == expected


class TestFilesystemFeatures:
    """Test filesystem feature detection."""

    def test_supports_symlinks(self):
        """Test symlink support detection."""
        supports = supports_symlinks()
        assert isinstance(supports, bool)

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    def test_windows_symlink_support(self, mock_is_windows):
        """Test Windows symlink support."""
        mock_is_windows.return_value = True

        supports = supports_symlinks()
        # Should be True for Python 3.8+
        expected = sys.version_info >= (3, 8)
        assert supports == expected

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    def test_unix_symlink_support(self, mock_is_windows):
        """Test Unix symlink support."""
        mock_is_windows.return_value = False

        supports = supports_symlinks()
        assert supports is True

    def test_is_case_sensitive_filesystem(self):
        """Test case sensitivity detection."""
        is_case_sensitive = is_case_sensitive_filesystem()
        assert isinstance(is_case_sensitive, bool)

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    def test_windows_case_sensitivity(self, mock_is_windows):
        """Test Windows case sensitivity."""
        mock_is_windows.return_value = True

        is_case_sensitive = is_case_sensitive_filesystem()
        assert is_case_sensitive is False

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    @patch("folder2md4llms.utils.platform_utils.is_macos")
    def test_macos_case_sensitivity(self, mock_is_macos, mock_is_windows):
        """Test macOS case sensitivity."""
        mock_is_windows.return_value = False
        mock_is_macos.return_value = True

        is_case_sensitive = is_case_sensitive_filesystem()
        assert is_case_sensitive is False

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    @patch("folder2md4llms.utils.platform_utils.is_macos")
    def test_linux_case_sensitivity(self, mock_is_macos, mock_is_windows):
        """Test Linux case sensitivity."""
        mock_is_windows.return_value = False
        mock_is_macos.return_value = False

        is_case_sensitive = is_case_sensitive_filesystem()
        assert is_case_sensitive is True


class TestPathHandling:
    """Test path handling utilities."""

    def test_get_path_separator(self):
        """Test getting path separator."""
        separator = get_path_separator()
        assert isinstance(separator, str)
        assert separator in ["\\", "/"]

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    def test_windows_path_separator(self, mock_is_windows):
        """Test Windows path separator."""
        mock_is_windows.return_value = True

        separator = get_path_separator()
        assert separator == "\\"

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    def test_unix_path_separator(self, mock_is_windows):
        """Test Unix path separator."""
        mock_is_windows.return_value = False

        separator = get_path_separator()
        assert separator == "/"

    def test_normalize_path(self):
        """Test path normalization."""
        # Test with mixed separators
        path = "folder/subfolder\\file.txt"
        normalized = normalize_path(path)
        assert isinstance(normalized, str)
        # Path normalization should result in consistent separators
        assert len(normalized) > 0

    def test_normalize_path_absolute(self):
        """Test normalizing absolute paths."""
        if is_windows():
            path = "C:\\Users\\test\\file.txt"
            normalized = normalize_path(path)
            assert normalized.startswith("C:")
        else:
            path = "/home/user/file.txt"
            normalized = normalize_path(path)
            assert normalized.startswith("/")

    def test_normalize_path_relative(self):
        """Test normalizing relative paths."""
        path = "relative/path/to/file.txt"
        normalized = normalize_path(path)
        assert not normalized.startswith("/")
        assert ":" not in normalized  # No drive letter


class TestSystemInfo:
    """Test system information utilities."""

    def test_get_line_ending(self):
        """Test getting line ending."""
        line_ending = get_line_ending()
        assert isinstance(line_ending, str)
        assert line_ending in ["\n", "\r\n"]

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    def test_windows_line_ending(self, mock_is_windows):
        """Test Windows line ending."""
        mock_is_windows.return_value = True

        line_ending = get_line_ending()
        assert line_ending == "\r\n"

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    def test_unix_line_ending(self, mock_is_windows):
        """Test Unix line ending."""
        mock_is_windows.return_value = False

        line_ending = get_line_ending()
        assert line_ending == "\n"

    def test_get_default_shell(self):
        """Test getting default shell."""
        shell = get_default_shell()
        assert isinstance(shell, str)
        assert len(shell) > 0

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    def test_windows_default_shell(self, mock_is_windows):
        """Test Windows default shell."""
        mock_is_windows.return_value = True

        shell = get_default_shell()
        assert shell == "cmd.exe"

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    def test_unix_default_shell(self, mock_is_windows):
        """Test Unix default shell."""
        mock_is_windows.return_value = False

        shell = get_default_shell()
        assert shell == "/bin/sh"

    def test_get_python_info(self):
        """Test getting Python information."""
        info = get_python_info()
        assert isinstance(info, dict)

        required_keys = [
            "version",
            "platform",
            "system",
            "machine",
            "processor",
            "python_implementation",
            "python_version",
        ]

        for key in required_keys:
            assert key in info
            assert isinstance(info[key], str)
            assert len(info[key]) > 0

    def test_python_info_values(self):
        """Test Python info values are reasonable."""
        info = get_python_info()

        # Check version format
        assert sys.version in info["version"]
        assert platform.platform() == info["platform"]
        assert platform.system() == info["system"]
        assert platform.machine() == info["machine"]
        assert platform.python_implementation() == info["python_implementation"]
        assert platform.python_version() == info["python_version"]


class TestLibrarySupport:
    """Test library support utilities."""

    def test_get_library_search_paths(self):
        """Test getting library search paths."""
        paths = get_library_search_paths()
        assert isinstance(paths, list)
        assert len(paths) > 0
        assert all(isinstance(path, str) for path in paths)

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    def test_windows_library_paths(self, mock_is_windows):
        """Test Windows library search paths."""
        mock_is_windows.return_value = True

        paths = get_library_search_paths()
        expected = [
            "C:\\Windows\\System32",
            "C:\\Windows\\SysWOW64",
            "C:\\Program Files",
            "C:\\Program Files (x86)",
        ]
        assert paths == expected

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    @patch("folder2md4llms.utils.platform_utils.is_macos")
    def test_macos_library_paths(self, mock_is_macos, mock_is_windows):
        """Test macOS library search paths."""
        mock_is_windows.return_value = False
        mock_is_macos.return_value = True

        paths = get_library_search_paths()
        expected = [
            "/usr/lib",
            "/usr/local/lib",
            "/opt/homebrew/lib",
            "/System/Library/Frameworks",
        ]
        assert paths == expected

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    @patch("folder2md4llms.utils.platform_utils.is_macos")
    def test_linux_library_paths(self, mock_is_macos, mock_is_windows):
        """Test Linux library search paths."""
        mock_is_windows.return_value = False
        mock_is_macos.return_value = False

        paths = get_library_search_paths()
        expected = [
            "/usr/lib",
            "/usr/local/lib",
            "/lib",
            "/lib64",
            "/usr/lib64",
        ]
        assert paths == expected

    def test_get_magic_library_name(self):
        """Test getting magic library name."""
        lib_name = get_magic_library_name()
        assert lib_name is not None
        assert isinstance(lib_name, str)
        assert lib_name in ["python-magic", "python-magic-bin"]

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    def test_windows_magic_library(self, mock_is_windows):
        """Test Windows magic library name."""
        mock_is_windows.return_value = True

        lib_name = get_magic_library_name()
        assert lib_name == "python-magic-bin"

    @patch("folder2md4llms.utils.platform_utils.is_windows")
    def test_unix_magic_library(self, mock_is_windows):
        """Test Unix magic library name."""
        mock_is_windows.return_value = False

        lib_name = get_magic_library_name()
        assert lib_name == "python-magic"


class TestCachedValues:
    """Test cached platform values."""

    def test_cached_platform_system(self):
        """Test that platform system is cached."""
        from folder2md4llms.utils.platform_utils import _platform_system

        assert isinstance(_platform_system, str)
        assert len(_platform_system) > 0
        assert _platform_system == platform.system().lower()

    def test_cached_platform_machine(self):
        """Test that platform machine is cached."""
        from folder2md4llms.utils.platform_utils import _platform_machine

        assert isinstance(_platform_machine, str)
        assert len(_platform_machine) > 0
        assert _platform_machine == platform.machine().lower()

    def test_cache_consistency(self):
        """Test that cached values are consistent across calls."""
        from folder2md4llms.utils.platform_utils import (
            _platform_machine,
            _platform_system,
        )
        from folder2md4llms.utils.platform_utils import _platform_machine as machine2

        # Import again to make sure values don't change
        from folder2md4llms.utils.platform_utils import _platform_system as system2

        assert _platform_system == system2
        assert _platform_machine == machine2


class TestIntegration:
    """Test integration scenarios."""

    def test_platform_specific_workflow(self):
        """Test a complete platform-specific workflow."""
        # Get platform info
        platform_name = get_platform_name()

        # Get platform-specific paths
        config_dir = get_config_directory()
        temp_dir = get_temp_directory()

        # Get platform-specific settings
        executable_exts = get_executable_extensions()
        library_paths = get_library_search_paths()
        magic_lib = get_magic_library_name()

        # Get platform-specific formatting
        path_sep = get_path_separator()
        line_ending = get_line_ending()
        shell = get_default_shell()

        # Get platform capabilities
        supports_links = supports_symlinks()
        case_sensitive = is_case_sensitive_filesystem()

        # Verify all values are appropriate
        assert isinstance(platform_name, str)
        assert isinstance(config_dir, Path)
        assert isinstance(temp_dir, Path)
        assert isinstance(executable_exts, set)
        assert isinstance(library_paths, list)
        assert isinstance(magic_lib, str)
        assert isinstance(path_sep, str)
        assert isinstance(line_ending, str)
        assert isinstance(shell, str)
        assert isinstance(supports_links, bool)
        assert isinstance(case_sensitive, bool)

        # Test path normalization with platform separator
        test_path = f"folder{path_sep}subfolder{path_sep}file.txt"
        normalized = normalize_path(test_path)
        assert isinstance(normalized, str)

    def test_cross_platform_compatibility(self):
        """Test that functions work across platforms."""
        # These functions should work on any platform
        functions_to_test = [
            get_platform_name,
            get_executable_extensions,
            get_temp_directory,
            get_config_directory,
            supports_symlinks,
            get_path_separator,
            get_line_ending,
            get_default_shell,
            get_library_search_paths,
            get_magic_library_name,
            is_case_sensitive_filesystem,
            get_python_info,
        ]

        for func in functions_to_test:
            result = func()
            assert result is not None
            assert result != ""
            assert result != []
            assert result != {}

    def test_path_operations_consistency(self):
        """Test that path operations are consistent."""
        # Test various path formats
        test_paths = [
            "simple.txt",
            "folder/file.txt",
            "folder\\file.txt",
            "./relative/path.txt",
            "../parent/file.txt",
        ]

        for path in test_paths:
            normalized = normalize_path(path)
            assert isinstance(normalized, str)
            assert len(normalized) > 0

            # Path normalization should be consistent
            assert normalized == str(Path(path))
