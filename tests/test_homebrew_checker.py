"""Tests for Homebrew update checker module."""

import subprocess
from unittest.mock import MagicMock, Mock, patch

from folder2md4llms.utils.homebrew_checker import (
    check_brew_outdated,
    check_formula_github,
    check_homebrew_update,
)


class TestHomebrewChecker:
    """Test suite for Homebrew update checker."""

    def test_check_brew_outdated_update_available(self):
        """Test brew outdated when update is available."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "folder2md4llms (0.2.1) < 0.2.2"

        with patch("subprocess.run", return_value=mock_result):
            result = check_brew_outdated()
            assert result == ("0.2.1", "0.2.2")

    def test_check_brew_outdated_up_to_date(self):
        """Test brew outdated when package is up to date."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result):
            result = check_brew_outdated()
            assert result is None

    def test_check_brew_outdated_not_installed(self):
        """Test brew outdated when brew is not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = check_brew_outdated()
            assert result is None

    def test_check_brew_outdated_timeout(self):
        """Test brew outdated with timeout."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("brew", 5)):
            result = check_brew_outdated()
            assert result is None

    def test_check_formula_github_success(self):
        """Test GitHub formula check with valid response."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'version "0.2.2"'
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False

        with patch(
            "folder2md4llms.utils.homebrew_checker.urlopen", return_value=mock_response
        ):
            result = check_formula_github()
            assert result == "0.2.2"

    def test_check_formula_github_url_version(self):
        """Test GitHub formula check parsing version from URL."""
        formula_content = b"""
        class Folder2md4llms < Formula
          desc "Convert folder structures to markdown"
          homepage "https://github.com/HenriquesLab/folder2md4llms"
          url "https://files.pythonhosted.org/packages/.../folder2md4llms-0.2.2.tar.gz"
        end
        """
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = formula_content
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False

        with patch(
            "folder2md4llms.utils.homebrew_checker.urlopen", return_value=mock_response
        ):
            result = check_formula_github()
            assert result == "0.2.2"

    def test_check_formula_github_failure(self):
        """Test GitHub formula check with network error."""
        with patch(
            "folder2md4llms.utils.homebrew_checker.urlopen",
            side_effect=Exception("Network error"),
        ):
            result = check_formula_github()
            assert result is None

    def test_check_homebrew_update_via_brew(self):
        """Test Homebrew update check via brew command."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "folder2md4llms (0.2.1) < 0.2.2"

        with patch("subprocess.run", return_value=mock_result):
            result = check_homebrew_update("0.2.1")
            assert result == (True, "0.2.2")

    def test_check_homebrew_update_via_github_fallback(self):
        """Test Homebrew update check falling back to GitHub."""
        # Mock brew command failure
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            # Mock GitHub success
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.read.return_value = b'version "0.2.2"'
            mock_response.__enter__.return_value = mock_response
            mock_response.__exit__.return_value = False

            with patch(
                "folder2md4llms.utils.homebrew_checker.urlopen",
                return_value=mock_response,
            ):
                result = check_homebrew_update("0.2.1")
                assert result == (True, "0.2.2")

    def test_check_homebrew_update_no_update(self):
        """Test Homebrew update check when no update available."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "folder2md4llms (0.2.2) < 0.2.2"

        with patch("subprocess.run", return_value=mock_result):
            result = check_homebrew_update("0.2.2")
            assert result == (False, "0.2.2")

    def test_check_homebrew_update_both_methods_fail(self):
        """Test Homebrew update check when both methods fail."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            with patch(
                "folder2md4llms.utils.homebrew_checker.urlopen",
                side_effect=Exception("Network error"),
            ):
                result = check_homebrew_update("0.2.1")
                assert result is None
