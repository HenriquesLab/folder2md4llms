"""
Installation method detection for folder2md4llms.

Detects how folder2md4llms was installed (Homebrew, pipx, uv, pip, etc.)
to provide appropriate upgrade instructions.
"""

import sys
from pathlib import Path
from typing import Literal

InstallMethod = Literal["homebrew", "pipx", "uv", "pip-user", "pip", "dev", "unknown"]


def detect_install_method() -> InstallMethod:
    """
    Detect how folder2md4llms was installed.

    Returns:
        Installation method: homebrew, pipx, uv, pip-user, pip, dev, or unknown
    """
    executable = Path(sys.executable).resolve()
    executable_str = str(executable)

    # Check for Homebrew installation
    # Common Homebrew prefixes on macOS and Linux
    homebrew_prefixes = [
        "/opt/homebrew",  # Apple Silicon Macs
        "/usr/local",  # Intel Macs and some Linux
        "/home/linuxbrew/.linuxbrew",  # Linux Homebrew
    ]

    for prefix in homebrew_prefixes:
        if executable_str.startswith(prefix):
            # Additional verification: check if Cellar path exists
            if "/Cellar/" in executable_str or "/opt/" in executable_str:
                return "homebrew"

    # Check for pipx installation
    # pipx typically installs to ~/.local/pipx/venvs/{package}/
    if (
        ".local/pipx/venvs/folder2md4llms" in executable_str
        or ".local/share/pipx/venvs/folder2md4llms" in executable_str
    ):
        return "pipx"

    # Check for uv tool installation
    # uv typically installs to ~/.local/share/uv/tools/{package}/
    if ".local/share/uv/tools/folder2md4llms" in executable_str:
        return "uv"

    # Check for development installation
    # Look for editable install markers or git repository
    try:
        import folder2md4llms

        package_path = Path(folder2md4llms.__file__).resolve().parent.parent.parent
        # Check if .git directory exists (dev install from git repo)
        if (package_path / ".git").exists():
            return "dev"
        # Check if .egg-info or .dist-info with "editable" marker exists
        for item in package_path.glob("*.egg-info"):
            if item.is_dir():
                return "dev"
    except Exception:  # nosec B110
        pass

    # Check for pip user installation
    # User site-packages typically in ~/.local/lib/python*/site-packages
    try:
        import site

        user_site = site.getusersitepackages()
        if user_site and user_site in executable_str:
            return "pip-user"
    except Exception:  # nosec B110
        pass

    # Check for system pip installation
    # System site-packages in /usr/lib or /usr/local/lib
    if "/site-packages/" in executable_str or "/dist-packages/" in executable_str:
        return "pip"

    return "unknown"


def get_upgrade_command(install_method: InstallMethod) -> str:
    """
    Get the appropriate upgrade command for the installation method.

    Args:
        install_method: The detected installation method

    Returns:
        Upgrade command string
    """
    commands = {
        "homebrew": "brew update && brew upgrade folder2md4llms",
        "pipx": "pipx upgrade folder2md4llms",
        "uv": "uv tool upgrade folder2md4llms",
        "pip-user": "pip install --upgrade --user folder2md4llms",
        "pip": "pip install --upgrade folder2md4llms",
        "dev": "cd <repo> && git pull && uv sync",
        "unknown": "pip install --upgrade folder2md4llms",
    }
    return commands[install_method]


def get_friendly_install_name(install_method: InstallMethod) -> str:
    """
    Get a user-friendly name for the installation method.

    Args:
        install_method: The detected installation method

    Returns:
        Friendly name string
    """
    names = {
        "homebrew": "Homebrew",
        "pipx": "pipx",
        "uv": "uv tool",
        "pip-user": "pip (user)",
        "pip": "pip",
        "dev": "Development mode",
        "unknown": "Unknown",
    }
    return names[install_method]
