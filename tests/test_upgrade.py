"""Tests for upgrade workflow integration."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from folder2md4llms.cli import main


class TestUpgradeCommand:
    """Test upgrade CLI command integration."""

    @patch("folder2md4llms.cli.handle_upgrade_workflow")
    def test_upgrade_check_flag(self, mock_workflow):
        """Test --upgrade-check flag invokes workflow correctly."""
        mock_workflow.return_value = (True, None)  # No update available

        runner = CliRunner()
        result = runner.invoke(main, ["--upgrade-check"])

        assert result.exit_code == 0
        mock_workflow.assert_called_once()
        call_kwargs = mock_workflow.call_args.kwargs
        assert call_kwargs["package_name"] == "folder2md4llms"
        assert call_kwargs["check_only"] is True
        assert call_kwargs["skip_confirmation"] is False
        assert call_kwargs["github_org"] == "henriqueslab"
        assert call_kwargs["github_repo"] == "folder2md4llms"

    @patch("folder2md4llms.cli.handle_upgrade_workflow")
    def test_upgrade_check_with_update_available(self, mock_workflow):
        """Test --upgrade-check when update is available."""
        mock_workflow.return_value = (False, None)  # Update available in check-only mode

        runner = CliRunner()
        result = runner.invoke(main, ["--upgrade-check"])

        assert result.exit_code == 0  # Should still exit 0 in check-only mode
        mock_workflow.assert_called_once()

    @patch("folder2md4llms.cli.handle_upgrade_workflow")
    def test_upgrade_flag(self, mock_workflow):
        """Test --upgrade flag invokes workflow correctly."""
        mock_workflow.return_value = (True, None)  # Successful upgrade

        runner = CliRunner()
        result = runner.invoke(main, ["--upgrade"])

        assert result.exit_code == 0
        mock_workflow.assert_called_once()
        call_kwargs = mock_workflow.call_args.kwargs
        assert call_kwargs["package_name"] == "folder2md4llms"
        assert call_kwargs["check_only"] is False
        assert call_kwargs["skip_confirmation"] is False

    @patch("folder2md4llms.cli.handle_upgrade_workflow")
    def test_upgrade_with_yes_flag(self, mock_workflow):
        """Test --upgrade --yes skips confirmation."""
        mock_workflow.return_value = (True, None)

        runner = CliRunner()
        result = runner.invoke(main, ["--upgrade", "--yes"])

        assert result.exit_code == 0
        mock_workflow.assert_called_once()
        call_kwargs = mock_workflow.call_args.kwargs
        assert call_kwargs["skip_confirmation"] is True

    @patch("folder2md4llms.cli.handle_upgrade_workflow")
    def test_upgrade_failure(self, mock_workflow):
        """Test upgrade failure exits with code 1."""
        mock_workflow.return_value = (False, "Upgrade failed: network error")

        runner = CliRunner()
        result = runner.invoke(main, ["--upgrade"])

        assert result.exit_code == 1
        mock_workflow.assert_called_once()

    @patch("folder2md4llms.cli.handle_upgrade_workflow")
    def test_upgrade_user_cancelled(self, mock_workflow):
        """Test upgrade when user cancels doesn't exit with error."""
        mock_workflow.return_value = (False, "User cancelled")

        runner = CliRunner()
        result = runner.invoke(main, ["--upgrade"])

        # User cancellation should still exit with code 1 (from sys.exit(1))
        assert result.exit_code == 1


class TestRichUpgradeNotifier:
    """Test RichUpgradeNotifier adapter."""

    def test_rich_notifier_implements_protocol(self):
        """Test that RichUpgradeNotifier implements all required methods."""
        from rich.console import Console

        from folder2md4llms.utils.rich_upgrade_notifier import RichUpgradeNotifier

        console = Console()
        notifier = RichUpgradeNotifier(console)

        # Check that all protocol methods exist
        assert hasattr(notifier, "show_checking")
        assert hasattr(notifier, "show_version_check")
        assert hasattr(notifier, "show_update_info")
        assert hasattr(notifier, "show_installer_info")
        assert hasattr(notifier, "show_success")
        assert hasattr(notifier, "show_error")
        assert hasattr(notifier, "show_manual_instructions")
        assert hasattr(notifier, "confirm_upgrade")

        # Check that methods are callable
        assert callable(notifier.show_checking)
        assert callable(notifier.show_version_check)
        assert callable(notifier.show_update_info)
        assert callable(notifier.show_installer_info)
        assert callable(notifier.show_success)
        assert callable(notifier.show_error)
        assert callable(notifier.show_manual_instructions)
        assert callable(notifier.confirm_upgrade)

    def test_rich_notifier_show_checking(self):
        """Test show_checking displays message."""
        from rich.console import Console

        from folder2md4llms.utils.rich_upgrade_notifier import RichUpgradeNotifier

        console = Console()
        notifier = RichUpgradeNotifier(console)

        # Should not raise any errors
        notifier.show_checking()

    def test_rich_notifier_show_version_check_no_update(self):
        """Test show_version_check when no update available."""
        from rich.console import Console

        from folder2md4llms.utils.rich_upgrade_notifier import RichUpgradeNotifier

        console = Console()
        notifier = RichUpgradeNotifier(console)

        # Should not raise any errors
        notifier.show_version_check("1.0.0", "1.0.0", False)

    def test_rich_notifier_show_version_check_update_available(self):
        """Test show_version_check when update is available."""
        from rich.console import Console

        from folder2md4llms.utils.rich_upgrade_notifier import RichUpgradeNotifier

        console = Console()
        notifier = RichUpgradeNotifier(console)

        # Should not raise any errors
        notifier.show_version_check("1.0.0", "1.1.0", True)

    @patch("click.confirm", return_value=True)
    def test_rich_notifier_confirm_upgrade_yes(self, mock_confirm):
        """Test confirm_upgrade returns True when user confirms."""
        from rich.console import Console

        from folder2md4llms.utils.rich_upgrade_notifier import RichUpgradeNotifier

        console = Console()
        notifier = RichUpgradeNotifier(console)

        result = notifier.confirm_upgrade("1.1.0")

        assert result is True
        mock_confirm.assert_called_once()

    @patch("click.confirm", return_value=False)
    def test_rich_notifier_confirm_upgrade_no(self, mock_confirm):
        """Test confirm_upgrade returns False when user declines."""
        from rich.console import Console

        from folder2md4llms.utils.rich_upgrade_notifier import RichUpgradeNotifier

        console = Console()
        notifier = RichUpgradeNotifier(console)

        result = notifier.confirm_upgrade("1.1.0")

        assert result is False

    @patch("click.confirm", side_effect=KeyboardInterrupt)
    def test_rich_notifier_confirm_upgrade_keyboard_interrupt(self, mock_confirm):
        """Test confirm_upgrade handles KeyboardInterrupt gracefully."""
        from rich.console import Console

        from folder2md4llms.utils.rich_upgrade_notifier import RichUpgradeNotifier

        console = Console()
        notifier = RichUpgradeNotifier(console)

        result = notifier.confirm_upgrade("1.1.0")

        assert result is False
