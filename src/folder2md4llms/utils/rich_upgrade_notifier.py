"""Rich console adapter for upgrade notifications."""

import click
from rich.console import Console


class RichUpgradeNotifier:
    """Adapt Rich console to UpgradeNotifier protocol for folder2md4llms."""

    def __init__(self, console: Console):
        """Initialize with Rich console instance.

        Args:
            console: Rich Console instance for styled output
        """
        self.console = console

    def show_checking(self) -> None:
        """Show 'checking for updates' message."""
        self.console.print("🔍 Checking for updates...", style="blue")

    def show_version_check(self, current: str, latest: str, available: bool) -> None:
        """Show version check results.

        Args:
            current: Current installed version
            latest: Latest available version
            available: Whether an update is available
        """
        self.console.print(f"Current version: [cyan]v{current}[/cyan]")
        if available:
            self.console.print(
                f"Latest version: [green bold]v{latest}[/green bold]"
            )
            self.console.print("✨ Update available!", style="yellow")
        else:
            self.console.print(
                "✓ You are already using the latest version", style="green"
            )

    def show_update_info(self, current: str, latest: str, release_url: str) -> None:
        """Show update available information.

        Args:
            current: Current version
            latest: Latest version
            release_url: URL to release notes
        """
        self.console.print()
        self.console.print(
            f"Update available: [cyan]v{current}[/cyan] → [green bold]v{latest}[/green bold]",
            style="yellow",
        )
        self.console.print(f"Release notes: [link]{release_url}[/link]")
        self.console.print()

    def show_installer_info(self, friendly_name: str, command: str) -> None:
        """Show detected installer information.

        Args:
            friendly_name: Human-readable installer name
            command: The upgrade command that will be executed
        """
        self.console.print()
        self.console.print(
            f"Detected installer: [bold]{friendly_name}[/bold]", style="blue"
        )
        self.console.print(f"Running: [yellow]{command}[/yellow]")
        self.console.print()

    def show_success(self, version: str) -> None:
        """Show successful upgrade message.

        Args:
            version: Version that was successfully installed
        """
        self.console.print()
        self.console.print(
            f"✓ Successfully upgraded to [green bold]v{version}[/green bold]",
            style="green",
        )
        self.console.print()
        self.console.print(
            "Please restart your terminal or reload your shell",
            style="yellow dim",
        )
        self.console.print(
            "to ensure the new version is loaded.", style="yellow dim"
        )

    def show_error(self, error: str | None) -> None:
        """Show upgrade error message.

        Args:
            error: Error message or None
        """
        self.console.print()
        self.console.print("✗ Upgrade failed", style="red bold")
        self.console.print()
        if error:
            self.console.print("Error:", style="red")
            self.console.print(error)
            self.console.print()

    def show_manual_instructions(self, install_method: str) -> None:
        """Show manual upgrade instructions.

        Args:
            install_method: The detected installation method
        """
        self.console.print("Manual upgrade:", style="yellow bold")
        if install_method == "homebrew":
            self.console.print("  [cyan]brew update && brew upgrade folder2md4llms[/cyan]")
        elif install_method == "pipx":
            self.console.print("  [cyan]pipx upgrade folder2md4llms[/cyan]")
        elif install_method == "uv":
            self.console.print("  [cyan]uv tool upgrade folder2md4llms[/cyan]")
        elif install_method == "dev":
            self.console.print(
                "  [cyan]cd <repo> && git pull && uv sync[/cyan]",
                style="dim",
            )
        else:
            self.console.print("  [cyan]pip install --upgrade folder2md4llms[/cyan]")
            self.console.print("  [dim]# Or with --user flag:[/dim]")
            self.console.print(
                "  [cyan]pip install --upgrade --user folder2md4llms[/cyan]"
            )

    def confirm_upgrade(self, version: str) -> bool:
        """Prompt user for confirmation using click.

        Args:
            version: Version to upgrade to

        Returns:
            True if user confirms, False otherwise
        """
        try:
            return click.confirm(
                f"Upgrade folder2md4llms to v{version}?", default=True
            )
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n⚠ Upgrade cancelled.", style="yellow")
            return False
