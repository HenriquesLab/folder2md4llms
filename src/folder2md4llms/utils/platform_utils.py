"""Platform-specific utilities for cross-platform compatibility."""

import platform
import sys
from pathlib import Path

# Cache platform info for performance
_platform_system = platform.system().lower()
_platform_machine = platform.machine().lower()


def is_windows() -> bool:
    """Check if running on Windows."""
    return _platform_system == "windows"


def is_macos() -> bool:
    """Check if running on macOS."""
    return _platform_system == "darwin"


def is_linux() -> bool:
    """Check if running on Linux."""
    return _platform_system == "linux"


def get_platform_name() -> str:
    """Get standardized platform name."""
    if is_windows():
        return "windows"
    elif is_macos():
        return "macos"
    elif is_linux():
        return "linux"
    else:
        return _platform_system


def get_executable_extensions() -> set:
    """Get platform-specific executable extensions."""
    if is_windows():
        return {".exe", ".bat", ".cmd", ".com", ".msi", ".dll"}
    elif is_macos():
        return {".app", ".dmg", ".pkg", ".dylib"}
    else:  # Linux and other Unix-like systems
        return {".so", ".deb", ".rpm", ".AppImage", ".bin", ".run"}


def get_temp_directory() -> Path:
    """Get platform-specific temporary directory."""
    if is_windows():
        import tempfile

        return Path(tempfile.gettempdir())
    else:
        import tempfile

        return Path(tempfile.gettempdir())  # nosec B108


def get_config_directory() -> Path:
    """Get platform-specific configuration directory."""
    if is_windows():
        appdata = Path.home() / "AppData" / "Roaming"
        return appdata / "folder2md4llms"
    elif is_macos():
        return Path.home() / "Library" / "Application Support" / "folder2md4llms"
    else:  # Linux
        xdg_config = Path.home() / ".config"
        return xdg_config / "folder2md4llms"


def supports_symlinks() -> bool:
    """Check if platform supports symbolic links."""
    if is_windows():
        # Windows supports symlinks but requires admin privileges or developer mode
        return sys.version_info >= (3, 8)  # Better symlink support in Python 3.8+
    else:
        return True


def get_path_separator() -> str:
    """Get platform-specific path separator."""
    return "\\" if is_windows() else "/"


def normalize_path(path: str) -> str:
    """Normalize path separators for the current platform."""
    return str(Path(path))


def get_line_ending() -> str:
    """Get platform-specific line ending."""
    return "\r\n" if is_windows() else "\n"


def get_default_shell() -> str:
    """Get platform-specific default shell."""
    if is_windows():
        return "cmd.exe"
    else:
        return "/bin/sh"


def get_library_search_paths() -> list:
    """Get platform-specific library search paths."""
    if is_windows():
        return [
            "C:\\Windows\\System32",
            "C:\\Windows\\SysWOW64",
            "C:\\Program Files",
            "C:\\Program Files (x86)",
        ]
    elif is_macos():
        return [
            "/usr/lib",
            "/usr/local/lib",
            "/opt/homebrew/lib",
            "/System/Library/Frameworks",
        ]
    else:  # Linux
        return [
            "/usr/lib",
            "/usr/local/lib",
            "/lib",
            "/lib64",
            "/usr/lib64",
        ]


def get_magic_library_name() -> str | None:
    """Get the appropriate magic library name for the platform."""
    if is_windows():
        # Windows typically uses python-magic-bin
        return "python-magic-bin"
    else:
        # Unix-like systems use python-magic
        return "python-magic"


def is_case_sensitive_filesystem() -> bool:
    """Check if the current filesystem is case-sensitive."""
    if is_windows():
        return False  # NTFS is case-insensitive by default
    elif is_macos():
        # macOS can be either, but HFS+ is case-insensitive by default
        # We could check the actual filesystem, but default to False for safety
        return False
    else:  # Linux and other Unix-like systems
        return True  # Most Unix filesystems are case-sensitive


def get_python_info() -> dict:
    """Get Python version and platform information."""
    return {
        "version": sys.version,
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
    }
