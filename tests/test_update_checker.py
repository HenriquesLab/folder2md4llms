"""Tests for the update checker module."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from folder2md4llms.utils.update_checker import UpdateChecker, check_for_updates

# Configure pytest-asyncio for specific async tests only


class TestUpdateChecker:
    """Test cases for UpdateChecker class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_file = self.temp_dir / "update_check.json"

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.fixture
    def update_checker(self):
        """Create an UpdateChecker instance for testing."""
        checker = UpdateChecker(check_interval=60)  # 1 minute for testing
        checker.cache_dir = self.temp_dir
        checker.cache_file = self.cache_file
        return checker

    def test_init(self, update_checker):
        """Test UpdateChecker initialization."""
        assert update_checker.check_interval == 60
        assert update_checker.cache_dir == self.temp_dir
        assert update_checker.cache_file == self.cache_file
        # Version should be a valid semantic version string
        import re

        version_pattern = r"^\d+\.\d+\.\d+(\.\w+\d*)?(\+[\w\d\.]+)?$"
        assert re.match(version_pattern, update_checker.current_version)

    def test_ensure_cache_dir(self, update_checker):
        """Test cache directory creation."""
        # Remove directory if it exists
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

        assert not self.temp_dir.exists()
        update_checker._ensure_cache_dir()
        assert self.temp_dir.exists()

    def test_load_cache_empty(self, update_checker):
        """Test loading cache when no cache file exists."""
        cache_data = update_checker._load_cache()
        assert cache_data == {}

    def test_load_cache_existing(self, update_checker):
        """Test loading existing cache data."""
        test_data = {
            "last_check": "2025-01-01T12:00:00",
            "latest_version": "1.0.0",
            "current_version": "0.9.0",
        }

        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        cache_data = update_checker._load_cache()
        assert cache_data == test_data

    def test_load_cache_invalid_json(self, update_checker):
        """Test loading cache with invalid JSON."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            f.write("invalid json")

        cache_data = update_checker._load_cache()
        assert cache_data == {}

    def test_save_cache(self, update_checker):
        """Test saving cache data."""
        test_data = {"last_check": "2025-01-01T12:00:00", "latest_version": "1.0.0"}

        update_checker._save_cache(test_data)

        assert self.cache_file.exists()
        with open(self.cache_file, encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data == test_data

    def test_should_check_for_updates_no_cache(self, update_checker):
        """Test should check when no cache exists."""
        assert update_checker._should_check_for_updates() is True

    def test_should_check_for_updates_old_cache(self, update_checker):
        """Test should check when cache is old."""
        old_time = datetime.now() - timedelta(hours=2)
        cache_data = {"last_check": old_time.isoformat()}
        update_checker._save_cache(cache_data)

        assert update_checker._should_check_for_updates() is True

    def test_should_check_for_updates_recent_cache(self, update_checker):
        """Test should not check when cache is recent."""
        recent_time = datetime.now() - timedelta(seconds=30)
        cache_data = {"last_check": recent_time.isoformat()}
        update_checker._save_cache(cache_data)

        assert update_checker._should_check_for_updates() is False

    def test_normalize_version_simple(self, update_checker):
        """Test version normalization for simple versions."""
        assert update_checker._normalize_version("1.2.3") == (1, 2, 3)
        assert update_checker._normalize_version("0.1.0") == (0, 1, 0)
        assert update_checker._normalize_version("10.20.30") == (10, 20, 30)

    def test_normalize_version_dev(self, update_checker):
        """Test version normalization for development versions."""
        version = "1.2.3.dev4+g909680c.d20250716"
        assert update_checker._normalize_version(version) == (1, 2, 3)

    def test_normalize_version_with_suffix(self, update_checker):
        """Test version normalization with suffixes."""
        assert update_checker._normalize_version("1.2.3rc1") == (1, 2, "3rc1")
        assert update_checker._normalize_version("1.2.3+build") == (1, 2, 3)

    def test_is_newer_version(self, update_checker):
        """Test version comparison."""
        # Get current version parts for dynamic testing
        current_version = update_checker.current_version
        current_normalized = update_checker._normalize_version(current_version)

        # Test with clearly newer versions
        assert update_checker._is_newer_version("99.0.0") is True
        assert update_checker._is_newer_version("10.0.0") is True

        # Test with clearly older versions
        assert update_checker._is_newer_version("0.1.0") is False
        assert update_checker._is_newer_version("0.0.1") is False

        # Test same version (should not be newer)
        clean_current = current_version.split(".dev")[0].split("+")[0]
        assert update_checker._is_newer_version(clean_current) is False

        # Test version with dev suffix (should not be newer than clean version)
        if "-dev" not in clean_current:
            assert update_checker._is_newer_version(f"{clean_current}-dev") is False

        # Test incremental versions based on current version
        if len(current_normalized) >= 3 and isinstance(current_normalized[2], int):
            # Test patch increment
            patch_increment = f"{current_normalized[0]}.{current_normalized[1]}.{current_normalized[2] + 1}"
            assert update_checker._is_newer_version(patch_increment) is True

            # Test patch decrement (should be older)
            if current_normalized[2] > 0:
                patch_decrement = f"{current_normalized[0]}.{current_normalized[1]}.{current_normalized[2] - 1}"
                assert update_checker._is_newer_version(patch_decrement) is False

        # Test minor increment
        if len(current_normalized) >= 2 and isinstance(current_normalized[1], int):
            minor_increment = f"{current_normalized[0]}.{current_normalized[1] + 1}.0"
            assert update_checker._is_newer_version(minor_increment) is True

        # Test major increment
        if len(current_normalized) >= 1 and isinstance(current_normalized[0], int):
            major_increment = f"{current_normalized[0] + 1}.0.0"
            assert update_checker._is_newer_version(major_increment) is True

        # Invalid versions should be handled gracefully
        assert update_checker._is_newer_version("invalid") is False
        assert update_checker._is_newer_version("") is False

    @pytest.mark.asyncio
    async def test_fetch_latest_version_success(self, update_checker):
        """Test successful version fetching from PyPI."""
        mock_response = Mock()
        mock_response.json.return_value = {"info": {"version": "1.0.0"}}
        mock_response.raise_for_status.return_value = None

        with patch("folder2md4llms.utils.update_checker.HTTPX_AVAILABLE", True):
            with patch(
                "folder2md4llms.utils.update_checker.httpx.AsyncClient"
            ) as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get.return_value = mock_response
                mock_client_class.return_value.__aenter__.return_value = mock_client

                version = await update_checker._fetch_latest_version()
                assert version == "1.0.0"

    @pytest.mark.asyncio
    async def test_fetch_latest_version_failure(self, update_checker):
        """Test version fetching failure."""
        with patch("folder2md4llms.utils.update_checker.HTTPX_AVAILABLE", True):
            with patch(
                "folder2md4llms.utils.update_checker.httpx.AsyncClient"
            ) as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get.side_effect = Exception("Network error")
                mock_client_class.return_value.__aenter__.return_value = mock_client

                version = await update_checker._fetch_latest_version()
                assert version is None

    @pytest.mark.asyncio
    async def test_fetch_latest_version_no_httpx(self, update_checker):
        """Test version fetching when httpx is not available."""
        with patch("folder2md4llms.utils.update_checker.HTTPX_AVAILABLE", False):
            version = await update_checker._fetch_latest_version()
            assert version is None

    def test_display_update_notification(self, update_checker):
        """Test update notification display."""
        with patch("folder2md4llms.utils.update_checker.console") as mock_console:
            update_checker._display_update_notification("1.0.0")

            # Check that console.print was called multiple times
            assert mock_console.print.call_count >= 5

            # Check that version information is in the calls
            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("1.0.0" in call for call in calls)
            assert any("Current version" in call for call in calls)

    @pytest.mark.asyncio
    async def test_check_for_updates_no_update(self, update_checker):
        """Test check when no update is available."""

        async def mock_fetch():
            return "0.3.0"

        with patch.object(
            update_checker, "_fetch_latest_version", side_effect=mock_fetch
        ):
            result = await update_checker.check_for_updates(force=True)
            assert result is None

    @pytest.mark.asyncio
    async def test_check_for_updates_with_update(self, update_checker):
        """Test check when update is available."""

        # Set current version to something lower than what we'll return
        update_checker.current_version = "0.3.1"

        async def mock_fetch():
            return "1.0.0"

        with patch.object(
            update_checker, "_fetch_latest_version", side_effect=mock_fetch
        ):
            result = await update_checker.check_for_updates(force=True)
            assert result == "1.0.0"

    @pytest.mark.asyncio
    async def test_check_for_updates_cached_result(self, update_checker):
        """Test check returns cached result when available."""
        # Set current version to something lower than what we'll return
        update_checker.current_version = "0.3.1"

        # Set up cache with newer version
        cache_data = {
            "last_check": datetime.now().isoformat(),
            "latest_version": "1.0.0",
            "current_version": "0.3.1",
        }
        update_checker._save_cache(cache_data)

        # Should return cached result without network call
        result = await update_checker.check_for_updates(force=False)
        assert result == "1.0.0"

    @pytest.mark.skip(reason="Event loop conflicts with pytest-asyncio environment")
    def test_check_for_updates_sync(self, update_checker):
        """Test synchronous wrapper for update checking."""

        # Mock the network call directly with a version that's newer than current
        async def mock_fetch():
            return "99.0.0"

        # Mock the _is_newer_version to always return True for this test
        with patch.object(
            update_checker, "_fetch_latest_version", side_effect=mock_fetch
        ):
            with patch.object(update_checker, "_is_newer_version", return_value=True):
                result = update_checker.check_for_updates_sync(
                    force=True, show_notification=False
                )
                assert result == "99.0.0"

    @pytest.mark.skip(reason="Event loop conflicts with pytest-asyncio environment")
    def test_check_for_updates_sync_with_notification(self, update_checker):
        """Test synchronous wrapper with notification display."""

        # Mock the network call directly with a version that's newer than current
        async def mock_fetch():
            return "99.0.0"

        # Mock the _is_newer_version to always return True for this test
        with patch.object(
            update_checker, "_fetch_latest_version", side_effect=mock_fetch
        ):
            with patch.object(update_checker, "_is_newer_version", return_value=True):
                with patch.object(
                    update_checker, "_display_update_notification"
                ) as mock_display:
                    result = update_checker.check_for_updates_sync(
                        force=True, show_notification=True
                    )
                    assert result == "99.0.0"
                    mock_display.assert_called_once_with("99.0.0")

    @pytest.mark.skip(reason="Event loop conflicts with pytest-asyncio environment")
    def test_check_for_updates_sync_no_update(self, update_checker):
        """Test synchronous wrapper when no update available."""

        # Mock the network call to return older version
        async def mock_fetch():
            return "0.3.0"

        with patch.object(
            update_checker, "_fetch_latest_version", side_effect=mock_fetch
        ):
            with patch.object(
                update_checker, "_display_update_notification"
            ) as mock_display:
                result = update_checker.check_for_updates_sync(
                    force=True, show_notification=True
                )
                assert result is None
                mock_display.assert_not_called()


class TestConvenienceFunction:
    """Test cases for the convenience function."""

    def test_check_for_updates_disabled(self):
        """Test convenience function when disabled."""
        result = check_for_updates(enabled=False)
        assert result is None

    def test_check_for_updates_enabled(self):
        """Test convenience function when enabled."""
        with patch(
            "folder2md4llms.utils.update_checker.UpdateChecker"
        ) as mock_checker_class:
            mock_checker = Mock()
            mock_checker.check_for_updates_sync.return_value = "1.0.0"
            mock_checker_class.return_value = mock_checker

            result = check_for_updates(
                enabled=True, force=True, show_notification=False, check_interval=3600
            )

            assert result == "1.0.0"
            mock_checker_class.assert_called_once_with(3600)
            mock_checker.check_for_updates_sync.assert_called_once_with(True, False)


class TestIntegration:
    """Integration tests for update checking."""

    @pytest.mark.skip(reason="Event loop issue in sync wrapper - needs investigation")
    def test_full_update_check_cycle(self):
        """Test a complete update check cycle."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            cache_file = cache_dir / "update_check.json"

            checker = UpdateChecker(check_interval=60)  # 60 seconds for testing
            checker.cache_dir = cache_dir
            checker.cache_file = cache_file

            # Mock network call to return newer version
            async def mock_fetch():
                return "1.0.0"

            with patch.object(checker, "_fetch_latest_version", side_effect=mock_fetch):
                # First check should find update and cache it
                result = checker.check_for_updates_sync(
                    force=True, show_notification=False
                )
                assert result == "1.0.0"

                # Cache file should exist
                assert cache_file.exists()

                # Second check should use cache (no network call)
                with patch.object(checker, "_fetch_latest_version") as mock_network:
                    result = checker.check_for_updates_sync(
                        force=False, show_notification=False
                    )
                    assert result == "1.0.0"
                    mock_network.assert_not_called()

    def test_error_handling_robustness(self):
        """Test that errors don't crash the application."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            checker = UpdateChecker()
            checker.cache_dir = cache_dir
            checker.cache_file = cache_dir / "update_check.json"

            # Test with various error conditions
            with patch.object(
                checker, "_fetch_latest_version", side_effect=Exception("Network error")
            ):
                result = checker.check_for_updates_sync(
                    force=True, show_notification=False
                )
                # Should return None and not crash
                assert result is None

            # Test with read-only cache directory
            cache_dir.chmod(0o444)  # Read-only
            try:
                result = checker.check_for_updates_sync(
                    force=True, show_notification=False
                )
                # Should not crash even if can't write cache
                assert result is None
            finally:
                cache_dir.chmod(0o755)  # Restore permissions
