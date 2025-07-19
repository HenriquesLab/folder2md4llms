"""Update checker module for folder2md4llms."""

import asyncio
import json
import os
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Union

import httpx
import rich
from packaging.version import Version
from rich.console import Console

from ..__version__ import __version__

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
        """Determine if we should check for updates based on cache."""
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
        console.print()
        console.print("📦 [bold cyan]Update Available![/bold cyan]")
        console.print(f"   Current version: [yellow]{self.current_version}[/yellow]")
        console.print(f"   Latest version:  [green]{latest_version}[/green]")
        console.print()
        console.print(
            "   To upgrade, run: [bold]pip install --upgrade folder2md4llms[/bold]"
        )
        console.print(
            "   Or with uv:      [bold]uv add --upgrade folder2md4llms[/bold]"
        )
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

        # Update cache
        cache_data = {
            "last_check": datetime.now().isoformat(),
            "latest_version": latest_version,
            "current_version": self.current_version,
        }
        self._save_cache(cache_data)

        if latest_version and self._is_newer_version(latest_version):
            return latest_version

        return None

    def check_for_updates_sync(
        self, force: bool = False, show_notification: bool = True
    ) -> str | None:
        """Synchronous wrapper for update checking.

        Args:
            force: Force check even if within check interval
            show_notification: Whether to display update notification

        Returns:
            Latest version if update available, None otherwise
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            latest_version = loop.run_until_complete(self.check_for_updates(force))
            if latest_version and show_notification:
                self._display_update_notification(latest_version)
            return latest_version
        except Exception:
            # Silently fail on any errors
            return None
        finally:
            # Don't close the loop if it was already running
            if not loop.is_running():
                loop.close()


def check_for_updates(
    enabled: bool = True,
    force: bool = False,
    show_notification: bool = True,
    check_interval: int = DEFAULT_CHECK_INTERVAL,
) -> str | None:
    """Convenience function to check for updates.

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

    checker = UpdateChecker(check_interval)
    return checker.check_for_updates_sync(force, show_notification)
