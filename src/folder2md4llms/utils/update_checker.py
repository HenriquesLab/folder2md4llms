"""Update checker module for folder2md4llms."""

import asyncio
import json
import os
import threading
from collections.abc import Coroutine
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from rich.console import Console

from ..__version__ import __version__
from .install_detector import (
    detect_install_method,
    get_friendly_install_name,
    get_upgrade_command,
)

# Constants
DEFAULT_CHECK_INTERVAL = 24 * 60 * 60  # 24 hours in seconds
CACHE_DIR = Path.home() / ".cache" / "folder2md4llms"
CACHE_FILE = CACHE_DIR / "update_check.json"
PYPI_API_URL = "https://pypi.org/pypi/folder2md4llms/json"
HTTPX_AVAILABLE = True

# Console for rich output
console = Console()


class UpdateChecker:
    """Handles checking for application updates from PyPI."""

    def __init__(self, check_interval: int = DEFAULT_CHECK_INTERVAL) -> None:
        """Initialize the update checker.

        Args:
            check_interval: Seconds between update checks (default: 24 hours)
        """
        self.check_interval = check_interval
        self.cache_dir = CACHE_DIR
        self.cache_file = CACHE_FILE
        self.current_version = __version__

    def _ensure_cache_dir(self) -> None:
        """Ensure the cache directory exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_cache(self) -> dict:
        """Load cached update check data."""
        if not self.cache_file.exists():
            return {}

        try:
            with open(self.cache_file, encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_cache(self, data: dict) -> None:
        """Save update check data to cache."""
        self._ensure_cache_dir()
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            # Silently fail if we can't write cache
            pass

    def _should_check_for_updates(self) -> bool:
        """Determine if we should check for updates based on cache and environment."""
        # Check environment variables for opt-out
        if os.getenv("FOLDER2MD4LLMS_NO_UPDATE_CHECK", "").lower() in (
            "1",
            "true",
            "yes",
        ):
            return False

        if os.getenv("NO_UPDATE_NOTIFIER", ""):
            return False

        cache_data = self._load_cache()
        last_check = cache_data.get("last_check")

        if not last_check:
            return True

        last_check_time = datetime.fromisoformat(last_check)
        time_since_check = datetime.now() - last_check_time

        return time_since_check > timedelta(seconds=self.check_interval)

    def _normalize_version(self, version: str) -> tuple:
        """Normalize a version string for comparison.

        Args:
            version: Version string like "1.2.3" or "1.2.3.dev4+g909680c.d20250716"

        Returns:
            Tuple of version parts for comparison
        """
        # Remove development/build suffixes for comparison
        clean_version = (
            version.split(".dev")[0]
            .split("+")[0]
            .split("-dev")[0]
            .split("-rc")[0]
            .split("-alpha")[0]
            .split("-beta")[0]
        )

        try:
            parts: list[int | str] = []
            for part in clean_version.split("."):
                try:
                    parts.append(int(part))
                except ValueError:
                    # Handle non-numeric parts (like "rc1")
                    parts.append(part)
            return tuple(parts)
        except Exception:
            # Fallback to string comparison if parsing fails
            return (clean_version,)

    def _is_newer_version(self, latest_version: str) -> bool:
        """Check if the latest version is newer than current version, handling mixed types."""
        try:
            current_normalized = self._normalize_version(self.current_version)
            latest_normalized = self._normalize_version(latest_version)

            # If either version contains only strings, it's likely invalid
            current_has_numbers = any(
                isinstance(part, int) for part in current_normalized
            )
            latest_has_numbers = any(
                isinstance(part, int) for part in latest_normalized
            )

            # If latest version has no numbers but current does, it's invalid
            if current_has_numbers and not latest_has_numbers:
                return False

            # If current version has no numbers but latest does, latest is newer
            if not current_has_numbers and latest_has_numbers:
                return True

            # Compare element-wise, handling int/str gracefully
            max_length = max(len(current_normalized), len(latest_normalized))

            for i in range(max_length):
                # Get current part, defaulting to 0 if index doesn't exist
                current_part = (
                    current_normalized[i] if i < len(current_normalized) else 0
                )
                latest_part = latest_normalized[i] if i < len(latest_normalized) else 0

                # Convert to same type for comparison
                if isinstance(current_part, int) and isinstance(latest_part, int):
                    if latest_part > current_part:
                        return True
                    if latest_part < current_part:
                        return False
                else:
                    # If types differ, convert both to str for comparison
                    current_str = str(current_part)
                    latest_str = str(latest_part)
                    if latest_str > current_str:
                        return True
                    if latest_str < current_str:
                        return False
            # If all compared equal, not newer
            return False
        except Exception:
            # If comparison fails, assume not newer
            return False

    async def _fetch_latest_version(self) -> str | None:
        """Fetch the latest version from PyPI API.

        Returns:
            Latest version string, or None if fetch failed
        """
        if not HTTPX_AVAILABLE:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(PYPI_API_URL)
                response.raise_for_status()
                data = response.json()
                if (
                    isinstance(data, dict)
                    and "info" in data
                    and "version" in data["info"]
                ):
                    version = data["info"]["version"]
                    return version if isinstance(version, str) else None
                return None
        except Exception:
            # Silently fail on any network/API errors
            return None

    def _display_update_notification(self, latest_version: str) -> None:
        """Display an update notification to the user.

        Args:
            latest_version: The latest available version
        """
        # Detect installation method and get appropriate upgrade command
        install_method = detect_install_method()
        upgrade_cmd = get_upgrade_command(install_method)
        install_name = get_friendly_install_name(install_method)

        console.print()
        console.print("📦 [bold cyan]Update Available![/bold cyan]")
        console.print(f"   Current version: [yellow]{self.current_version}[/yellow]")
        console.print(f"   Latest version:  [green]{latest_version}[/green]")
        console.print(f"   Installed via:   [blue]{install_name}[/blue]")
        console.print()
        console.print("   To upgrade, run:")
        console.print(f"   [bold]{upgrade_cmd}[/bold]")
        console.print()

    async def check_for_updates(self, force: bool = False) -> str | None:
        """Check for available updates.

        Args:
            force: Force check even if within check interval

        Returns:
            Latest version if update available, None otherwise
        """
        if not force and not self._should_check_for_updates():
            # Check cache for previously found update
            cache_data = self._load_cache()
            cached_latest = cache_data.get("latest_version")
            if (
                cached_latest
                and isinstance(cached_latest, str)
                and self._is_newer_version(cached_latest)
            ):
                return str(cached_latest)
            return None

        latest_version = await self._fetch_latest_version()

        # Determine if update is available
        update_available = False
        if latest_version and self._is_newer_version(latest_version):
            update_available = True

        # Update cache
        cache_data = {
            "last_check": datetime.now().isoformat(),
            "latest_version": latest_version,
            "current_version": self.current_version,
            "update_available": update_available,
        }
        self._save_cache(cache_data)

        if update_available:
            return latest_version

        return None

    def check_for_updates_async(self, force: bool = False) -> None:
        """Check for updates in a background thread (non-blocking).

        This method starts an async update check in the background without blocking
        the main thread. Results are cached for later display.

        Args:
            force: Force check even if within check interval
        """
        if not force and not self._should_check_for_updates():
            return

        def _check():
            """Internal function to run async check in thread."""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.check_for_updates(force))
                finally:
                    loop.close()
            except Exception:  # nosec B110
                # Silently fail to avoid disrupting main application
                pass

        # Run check in background thread (daemon, non-blocking)
        thread = threading.Thread(target=_check, daemon=True)
        thread.start()
        # Don't join() - let it run in background

    def get_update_notification(self) -> str | None:
        """Get update notification message from cache.

        Returns:
            Notification message if update available, None otherwise
        """
        cache_data = self._load_cache()
        if not cache_data or not cache_data.get("update_available"):
            return None

        latest_version = cache_data.get("latest_version")
        if not latest_version:
            return None

        # Detect installation method
        install_method = detect_install_method()
        upgrade_cmd = get_upgrade_command(install_method)
        install_name = get_friendly_install_name(install_method)

        # Build notification message
        notification = [
            "",
            "─" * 60,
            f"📦 Update available: folder2md4llms v{self.current_version} → v{latest_version}",
            "",
            f"   Installed via: {install_name}",
            f"   To upgrade, run: {upgrade_cmd}",
            "",
            f"   Release notes: https://github.com/henriqueslab/folder2md4llms/releases/tag/v{latest_version}",
            "─" * 60,
        ]

        return "\n".join(notification)

    def show_update_notification(self) -> None:
        """Display update notification from cache if available."""
        notification = self.get_update_notification()
        if notification:
            console.print(notification)

    def _run_async_in_thread(self, coro: Coroutine[Any, Any, str | None]) -> str | None:
        """Run an async coroutine in a separate thread with its own event loop.

        This method prevents RuntimeError: This event loop is already running
        by isolating the async operation in a dedicated thread.

        Args:
            coro: The coroutine to execute

        Returns:
            Result from the coroutine, or None if execution failed
        """
        result = None
        exception = None

        def run_in_thread():
            nonlocal result, exception
            try:
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(coro)
                finally:
                    loop.close()
            except Exception as e:
                exception = e

        # Run the coroutine in a separate thread
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        thread.join(timeout=30)  # 30 second timeout

        if thread.is_alive():
            # Thread is still running after timeout
            return None

        if exception is not None:
            # Re-raise the exception from the thread
            raise exception

        return result

    def check_for_updates_sync(
        self, force: bool = False, show_notification: bool = True
    ) -> str | None:
        """Synchronous wrapper for update checking.

        This method safely handles async operations by running them in a separate
        thread with their own event loop, preventing conflicts with existing
        event loops.

        Args:
            force: Force check even if within check interval
            show_notification: Whether to display update notification

        Returns:
            Latest version if update available, None otherwise
        """
        try:
            # Check if we can use asyncio.run directly (no running loop)
            try:
                asyncio.get_running_loop()
                # We have a running loop, so use thread-based approach
                latest_version = self._run_async_in_thread(
                    self.check_for_updates(force)
                )
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                latest_version = asyncio.run(self.check_for_updates(force))

            if latest_version and show_notification:
                self._display_update_notification(latest_version)
            return latest_version
        except Exception:
            # Silently fail on any errors to avoid disrupting the main application
            return None


# Global instance for singleton pattern
_update_checker: UpdateChecker | None = None


def get_update_checker(check_interval: int = DEFAULT_CHECK_INTERVAL) -> UpdateChecker:
    """Get the global update checker instance (singleton).

    Args:
        check_interval: Seconds between update checks

    Returns:
        UpdateChecker instance
    """
    global _update_checker
    if _update_checker is None:
        _update_checker = UpdateChecker(check_interval)
    return _update_checker


def check_for_updates(
    enabled: bool = True,
    force: bool = False,
    show_notification: bool = True,
    check_interval: int = DEFAULT_CHECK_INTERVAL,
) -> str | None:
    """Convenience function to check for updates (synchronous, blocking).

    Args:
        enabled: Whether update checking is enabled
        force: Force check even if within check interval
        show_notification: Whether to display update notification
        check_interval: Seconds between update checks

    Returns:
        Latest version if update available, None otherwise
    """
    if not enabled:
        return None

    checker = get_update_checker(check_interval)
    return checker.check_for_updates_sync(force, show_notification)


def check_for_updates_async_background(
    enabled: bool = True,
    force: bool = False,
    check_interval: int = DEFAULT_CHECK_INTERVAL,
) -> None:
    """Start async update check in background (non-blocking).

    This is the recommended way to check for updates without blocking the CLI.
    Results are cached and can be displayed later with show_update_notification().

    Args:
        enabled: Whether update checking is enabled
        force: Force check even if within check interval
        check_interval: Seconds between update checks
    """
    if not enabled:
        return

    checker = get_update_checker(check_interval)
    checker.check_for_updates_async(force)


def show_update_notification() -> None:
    """Display cached update notification if available."""
    checker = get_update_checker()
    checker.show_update_notification()
