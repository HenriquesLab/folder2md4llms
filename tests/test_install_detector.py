"""Tests for installation detection module."""

from unittest.mock import patch

from folder2md4llms.utils.install_detector import (
    detect_install_method,
    get_friendly_install_name,
    get_upgrade_command,
)


class TestInstallDetector:
    """Test suite for install detector."""

    def test_homebrew_detection_apple_silicon(self):
        """Test Homebrew detection on Apple Silicon Mac."""
        with patch(
            "sys.executable", "/opt/homebrew/Cellar/folder2md4llms/0.2.1/bin/python3"
        ):
            result = detect_install_method()
            assert result == "homebrew"

    def test_homebrew_detection_intel(self):
        """Test Homebrew detection on Intel Mac."""
        with patch(
            "sys.executable", "/usr/local/Cellar/folder2md4llms/0.2.1/bin/python3"
        ):
            result = detect_install_method()
            assert result == "homebrew"

    def test_pipx_detection(self):
        """Test pipx installation detection."""
        with patch(
            "sys.executable",
            "/home/user/.local/pipx/venvs/folder2md4llms/bin/python",
        ):
            result = detect_install_method()
            assert result == "pipx"

    def test_uv_detection(self):
        """Test uv tool installation detection."""
        with patch(
            "sys.executable",
            "/home/user/.local/share/uv/tools/folder2md4llms/bin/python",
        ):
            result = detect_install_method()
            assert result == "uv"

    def test_pip_detection(self):
        """Test pip installation detection."""
        with patch(
            "sys.executable",
            "/usr/lib/python3.11/site-packages/python",
        ):
            # Mock the Path.exists to prevent dev detection
            with patch("pathlib.Path.exists", return_value=False):
                result = detect_install_method()
                assert result == "pip"

    def test_get_upgrade_command_homebrew(self):
        """Test upgrade command for Homebrew."""
        cmd = get_upgrade_command("homebrew")
        assert cmd == "brew update && brew upgrade folder2md4llms"

    def test_get_upgrade_command_pipx(self):
        """Test upgrade command for pipx."""
        cmd = get_upgrade_command("pipx")
        assert cmd == "pipx upgrade folder2md4llms"

    def test_get_upgrade_command_uv(self):
        """Test upgrade command for uv."""
        cmd = get_upgrade_command("uv")
        assert cmd == "uv tool upgrade folder2md4llms"

    def test_get_friendly_name_homebrew(self):
        """Test friendly name for Homebrew."""
        name = get_friendly_install_name("homebrew")
        assert name == "Homebrew"

    def test_get_friendly_name_pipx(self):
        """Test friendly name for pipx."""
        name = get_friendly_install_name("pipx")
        assert name == "pipx"

    def test_get_friendly_name_unknown(self):
        """Test friendly name for unknown method."""
        name = get_friendly_install_name("unknown")
        assert name == "Unknown"
