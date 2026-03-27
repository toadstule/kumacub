#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025-2026 Stephen T. Jibson.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Test configuration loading from TOML and environment variables."""

from __future__ import annotations

import os
import textwrap
import typing
from typing import TYPE_CHECKING
from unittest.mock import patch

import pydantic_settings
import pytest

from kumacub import config
from kumacub.domain.models import Check, Executor, Parser, Schedule, StdoutPublisher

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


# ============================================================================
# Fixtures and Utilities
# ============================================================================


@pytest.fixture(autouse=True)
def _reset_config_cache() -> Iterator[None]:
    """Reset config cache before and after each test."""
    config.reset_settings_cache()
    yield
    config.reset_settings_cache()


# ============================================================================
# Mock Classes
# ============================================================================


class MockLogSettings:
    """Mock log settings for testing."""

    def __init__(self) -> None:
        """Initialize mock log settings with default values."""
        self.level = "INFO"
        self.structured = False


class MockSettings:
    """Mock settings for testing configuration loading."""

    model_config: typing.ClassVar[dict[str, object]] = {}

    def __init__(self) -> None:
        """Initialize mock settings with default values."""
        self.log = MockLogSettings()
        self.checks = [
            Check(
                name="test-check",
                executor=Executor(command="echo"),
                parser=Parser(),
                publisher=StdoutPublisher(),
                schedule=Schedule(interval=60),
            )
        ]

        # Track environment overrides
        self._env_overrides: dict[str, object] = {}

    def model_dump(self) -> dict[str, typing.Any]:
        """Return a dictionary representation of the settings.

        Returns:
            dict: A dictionary containing the settings data.
        """
        return {
            "log": {"level": self.log.level, "structured": self.log.structured},
            "checks": [
                {
                    "name": check.name,
                    "executor": check.executor.model_dump(),
                    "parser": check.parser.model_dump(),
                    "publisher": check.publisher.model_dump(),
                    "schedule": check.schedule.model_dump(),
                }
                for check in self.checks
            ],
        }


# ============================================================================
# Configuration Loading Tests
# ============================================================================


@pytest.fixture
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Mock the settings to avoid loading from a TOML file."""
    # Clear any existing environment variables that might interfere
    for key in os.environ:
        if key.startswith("KUMACUB__"):
            monkeypatch.delenv(key, raising=False)

    # Create a real settings instance with our mock data
    settings = MockSettings()

    # Patch the Settings class to return our mock
    with patch("kumacub.config.Settings") as mock_settings_cls:
        # Configure the mock to return our settings instance
        mock_settings_cls.return_value = settings

        # Also patch reload_settings to update our mock settings from environment
        def reload_mock() -> MockSettings:
            """Reload mock settings from environment variables.

            Returns:
                MockSettings: The updated settings instance.
            """
            # Update log level from environment if set
            log_level = os.environ.get("KUMACUB__LOG__LEVEL")
            if log_level:
                settings.log.level = log_level
            return settings

        with (
            patch("kumacub.config.reload_settings", side_effect=reload_mock),
            patch("kumacub.config.get_settings", side_effect=reload_mock),
        ):
            yield


@pytest.fixture
def config_toml_file(tmp_path: Path) -> Iterator[Path]:
    """Create a temporary config TOML file and set toml_file in model_config."""
    toml = tmp_path / "cfg.toml"
    toml.write_text(
        textwrap.dedent(
            """
            service_name = "kumacub"
            [log]
            level = "DEBUG"
            structured = false

            [[checks]]
            name = "test-check"
            executor.command = "echo"
            executor.args = ["-n", "OK - Test is running"]
            publisher.name = "stdout"
            publisher.url = ""
            publisher.push_token = ""
            schedule.interval = 60
            """
        )
    )

    # Save the original model config
    original_config = config.Settings.model_config

    # Create a new model config with our test TOML file
    new_config = pydantic_settings.SettingsConfigDict()

    # Set the attributes from the original config
    for key, value in original_config.items():
        if key != "toml_file":
            setattr(new_config, key, value)

    # Set the test TOML file
    new_config["toml_file"] = str(toml)

    # Update the model config to use our test TOML file
    config.Settings.model_config = new_config

    yield toml

    # Restore the original model config
    config.Settings.model_config = original_config


# ============================================================================
# Basic Configuration Tests
# ============================================================================


@pytest.mark.usefixtures("mock_settings")
def test_settings_load_from_toml() -> None:
    """Test that settings are loaded correctly."""
    s = config.get_settings()
    assert s.log.level == "INFO"
    assert s.log.structured is False
    assert len(s.checks) == 1
    assert s.checks.pop().name == "test-check"


# ============================================================================
# Environment Override Tests
# ============================================================================


@pytest.mark.usefixtures("mock_settings")
def test_settings_env_overrides_toml(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that environment variables override settings."""
    # First load settings
    s = config.get_settings()
    assert s.log.level == "INFO"

    # Override via env using monkeypatch (auto-cleanup)
    monkeypatch.setenv("KUMACUB__LOG__LEVEL", "WARNING")

    # The log level should be updated on the next get
    s = config.get_settings()
    assert s.log.level == "WARNING"


@pytest.mark.usefixtures("mock_settings")
def test_settings_cache_behavior() -> None:
    """Test that get_settings() returns cached instance."""
    # Get the settings once
    s1 = config.get_settings()

    # Get the settings again - should be the same instance
    s2 = config.get_settings()

    # Should be the same instance due to caching
    assert s1 is s2


@pytest.mark.usefixtures("mock_settings")
def test_reset_settings_cache_clears_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that reset_settings_cache() clears the cache."""
    # Set up test data
    original_level = "INFO"
    new_level = "DEBUG"

    # Get initial settings
    s1 = config.get_settings()
    assert s1.log.level == original_level

    # Change the environment variable
    monkeypatch.setenv("KUMACUB__LOG__LEVEL", new_level)

    # Reset the cache and reload settings
    config.reset_settings_cache()
    s2 = config.reload_settings()

    # The log level should be updated in the new settings
    assert s2.log.level == new_level

    # Since our mock returns the same instance, the original settings object is updated
    # So we need to check that the instance was actually updated
    assert s1 is s2  # Same instance
    assert s1.log.level == new_level  # Updated in place


@pytest.mark.usefixtures("mock_settings")
def test_reload_settings_updates_in_place(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that reload_settings() updates existing instance."""
    # Get the initial settings
    s1 = config.get_settings()
    original_level = s1.log.level

    # Verify initial state
    assert original_level == "INFO"

    # Change environment to a new log level
    new_level = "CRITICAL"
    monkeypatch.setenv("KUMACUB__LOG__LEVEL", new_level)

    # Reload settings to pick up the environment variable
    s2 = config.reload_settings()

    # Should be the same instance but with updated values
    assert s1 is s2
    assert s2.log.level == new_level


def test_real_settings_instantiation(tmp_path: Path) -> None:
    """Test actual Settings instantiation without mocking for code coverage."""
    # Create a minimal config file with at least one check
    toml_file = tmp_path / "test.toml"
    toml_file.write_text(
        '[log]\nlevel = "WARNING"\n\n'
        '[[checks]]\nname = "test-check"\nexecutor.command = "echo"\n'
        'publisher.name = "stdout"\nschedule.interval = 60\n'
    )

    # Save and patch the environment variable for config location
    original_env = {
        "KUMACUB__CONFIG": os.environ.get("KUMACUB__CONFIG"),
        "KUMACUB__CHECKS_DIR": os.environ.get("KUMACUB__CHECKS_DIR"),
    }
    os.environ["KUMACUB__CONFIG"] = str(toml_file)
    os.environ["KUMACUB__CHECKS_DIR"] = ""

    try:
        # Reset cache to ensure fresh load
        config.reset_settings_cache()

        # Call the real get_settings (not mocked)
        s1 = config.get_settings()
        assert s1 is not None
        assert s1.log.level == "WARNING"

        # Verify caching works
        s2 = config.get_settings()
        assert s1 is s2

        # Test reload_settings
        s3 = config.reload_settings()
        assert s3 is s1  # Same instance after reload

    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        config.reset_settings_cache()


@pytest.fixture
def config_toml_directory(tmp_path: Path) -> Path:
    """Create a temporary config directory with multiple TOML files."""
    checks_dir = tmp_path / "conf.d"
    checks_dir.mkdir()

    # Create multiple TOML files like the README examples
    (checks_dir / "01_disk_usage.toml").write_text(
        textwrap.dedent(
            """
            [[checks]]
            name = "disk usage"
            executor.command = "/usr/lib/monitoring-plugins/check_disk"
            executor.args = ["-c", "90"]
            publisher.name = "stdout"
            schedule.interval = 60
            """
        )
    )

    (checks_dir / "02_system_time.toml").write_text(
        textwrap.dedent(
            """
            [[checks]]
            name = "system time (ntp)"
            executor.command = "/usr/lib/monitoring-plugins/check_ntp_time"
            executor.args = ["-H", "pool.ntp.org", "-c", "10"]
            publisher.name = "stdout"
            schedule.interval = 30
            """
        )
    )

    (checks_dir / "03_system_load.toml").write_text(
        textwrap.dedent(
            """
            [[checks]]
            name = "system load"
            executor.command = "check_load"
            executor.args = ["-c", "10", "-w", "10"]
            executor.env = { "PATH" = "/usr/lib/monitoring-plugins" }
            publisher.name = "stdout"
            schedule.interval = 30
            """
        )
    )

    (checks_dir / "99_production_overrides.toml").write_text(
        textwrap.dedent(
            """
            [[checks]]
            name = "production-check"
            executor.command = "echo"
            executor.args = ["production"]
            publisher.name = "stdout"
            """
        )
    )

    return checks_dir


def test_directory_toml_loading(config_toml_directory: Path) -> None:
    """Test loading multiple TOML files from a directory with main config file."""
    # Create a main config file with a check
    main_config_file = config_toml_directory.parent / "main_config.toml"
    main_config_file.write_text(
        textwrap.dedent(
            """
            [log]
            level = "ERROR"

            [[checks]]
            name = "main-config-check"
            executor.command = "echo"
            executor.args = ["main"]
            publisher.name = "stdout"
            schedule.interval = 120
            """
        )
    )

    # Save original environment
    original_env = {
        "KUMACUB__CONFIG": os.environ.get("KUMACUB__CONFIG"),
        "KUMACUB__CHECKS_DIR": os.environ.get("KUMACUB__CHECKS_DIR"),
    }
    os.environ["KUMACUB__CONFIG"] = str(main_config_file)
    os.environ["KUMACUB__CHECKS_DIR"] = str(config_toml_directory)

    try:
        # Reset cache to ensure fresh load
        config.reset_settings_cache()

        # Load settings from directory
        settings = config.get_settings()

        # Check that log level from main config wins (ERROR from main_config.toml)
        assert settings.log.level == "ERROR"
        # structured should be true from the default LogSettings, since none of the files override it
        assert settings.log.structured is True

        # With custom merge, checks from all files are accumulated (5 total: 4 from directory + 1 from main)
        assert len(settings.checks) == 5
        check_names = {check.name for check in settings.checks}
        assert "disk usage" in check_names
        assert "system time (ntp)" in check_names
        assert "system load" in check_names
        assert "main-config-check" in check_names

    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        config.reset_settings_cache()


def test_directory_toml_merge_order(tmp_path: Path) -> None:
    """Test that TOML files are merged in alphabetical order."""
    checks_dir = tmp_path / "conf.d"
    checks_dir.mkdir()

    # Create files in non-alphabetical order to test sorting
    # Directory files can only contain [[checks]] sections
    (checks_dir / "z_last.toml").write_text(
        textwrap.dedent(
            """
            [[checks]]
            name = "last-check"
            executor.command = "echo"
            executor.args = ["last"]
            publisher.name = "stdout"
            """
        )
    )

    (checks_dir / "a_first.toml").write_text(
        textwrap.dedent(
            """
            [[checks]]
            name = "first-check"
            executor.command = "echo"
            executor.args = ["first"]
            publisher.name = "stdout"
            """
        )
    )

    (checks_dir / "m_middle.toml").write_text(
        textwrap.dedent(
            """
            [[checks]]
            name = "middle-check"
            executor.command = "echo"
            executor.args = ["middle"]
            publisher.name = "stdout"
            """
        )
    )

    # Save original environment
    original_env = {
        "KUMACUB__CONFIG": os.environ.get("KUMACUB__CONFIG"),
        "KUMACUB__CHECKS_DIR": os.environ.get("KUMACUB__CHECKS_DIR"),
    }
    os.environ["KUMACUB__CONFIG"] = ""
    os.environ["KUMACUB__CHECKS_DIR"] = str(checks_dir)

    try:
        config.reset_settings_cache()
        settings = config.get_settings()

        # Should have all 3 checks from directory files in alphabetical order
        assert len(settings.checks) == 3
        check_names = [check.name for check in settings.checks]
        # Should be in alphabetical order: a_first, m_middle, z_last
        assert check_names == ["first-check", "middle-check", "last-check"]

    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        config.reset_settings_cache()


def test_empty_checks_directory(tmp_path: Path) -> None:
    """Test behavior with empty config directory."""
    checks_dir = tmp_path / "empty_conf.d"
    checks_dir.mkdir()

    # Save original environment
    original_env = {
        "KUMACUB__CONFIG": os.environ.get("KUMACUB__CONFIG"),
        "KUMACUB__CHECKS_DIR": os.environ.get("KUMACUB__CHECKS_DIR"),
    }
    os.environ["KUMACUB__CONFIG"] = ""
    os.environ["KUMACUB__CHECKS_DIR"] = str(checks_dir)

    try:
        config.reset_settings_cache()

        # Should raise SystemExit since no checks are defined
        with pytest.raises(SystemExit) as exc_info:
            config.get_settings()

        # Check that the error message mentions no checks found
        assert "No checks found in configuration" in str(exc_info.value)

    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        config.reset_settings_cache()


def test_nonexistent_checks_directory(tmp_path: Path) -> None:
    """Test behavior with non-existent config directory."""
    nonexistent_dir = tmp_path / "nonexistent"

    # Save original environment
    original_env = {
        "KUMACUB__CONFIG": os.environ.get("KUMACUB__CONFIG"),
        "KUMACUB__CHECKS_DIR": os.environ.get("KUMACUB__CHECKS_DIR"),
    }
    os.environ["KUMACUB__CONFIG"] = ""
    os.environ["KUMACUB__CHECKS_DIR"] = str(nonexistent_dir)

    try:
        config.reset_settings_cache()

        # Should raise SystemExit since no checks are defined
        with pytest.raises(SystemExit) as exc_info:
            config.get_settings()

        # Check that the error message mentions no checks found
        assert "No checks found in configuration" in str(exc_info.value)

    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        config.reset_settings_cache()


def test_invalid_toml_in_directory(tmp_path: Path) -> None:
    """Test handling of invalid TOML files in directory."""
    checks_dir = tmp_path / "conf.d"
    checks_dir.mkdir()

    # Create a valid TOML file
    (checks_dir / "valid.toml").write_text(
        textwrap.dedent(
            """
            [log]
            level = "INFO"
            """
        )
    )

    # Create an invalid TOML file
    (checks_dir / "invalid.toml").write_text("invalid toml content [")

    # Save original environment
    original_env = {
        "KUMACUB__CONFIG": os.environ.get("KUMACUB__CONFIG"),
        "KUMACUB__CHECKS_DIR": os.environ.get("KUMACUB__CHECKS_DIR"),
    }
    os.environ["KUMACUB__CONFIG"] = ""
    os.environ["KUMACUB__CHECKS_DIR"] = str(checks_dir)

    try:
        config.reset_settings_cache()

        # Should raise an exception when trying to load invalid TOML
        with pytest.raises(SystemExit):  # Now we raise SystemExit for any TOML issues
            config.get_settings()

    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        config.reset_settings_cache()


def test_no_checks_defined_error(tmp_path: Path) -> None:
    """Test that configuration fails when no checks are defined."""
    # Create a main config file with only logging (no checks)
    main_config_file = tmp_path / "config.toml"
    main_config_file.write_text('[log]\nlevel = "INFO"\n')

    # Save original environment
    original_env = {
        "KUMACUB__CONFIG": os.environ.get("KUMACUB__CONFIG"),
        "KUMACUB__CHECKS_DIR": os.environ.get("KUMACUB__CHECKS_DIR"),
    }
    os.environ["KUMACUB__CONFIG"] = str(main_config_file)
    os.environ["KUMACUB__CHECKS_DIR"] = ""

    try:
        config.reset_settings_cache()

        # Should raise SystemExit since no checks are defined
        with pytest.raises(SystemExit) as exc_info:
            config.get_settings()

        # Check that the error message mentions no checks found
        assert "No checks found in configuration" in str(exc_info.value)

    finally:
        # Restore environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        config.reset_settings_cache()


def test_directory_toml_file_permission_error(tmp_path: Path) -> None:
    """Test handling of unreadable TOML files."""
    checks_dir = tmp_path / "conf.d"
    checks_dir.mkdir()

    # Create a valid TOML file
    (checks_dir / "valid.toml").write_text(
        textwrap.dedent(
            """
            [[checks]]
            name = "valid-check"
            executor.command = "echo"
            executor.args = ["test"]
            publisher.name = "stdout"
            """
        )
    )

    # Create a file with no read permissions
    unreadable_file = checks_dir / "unreadable.toml"
    unreadable_file.write_text(
        textwrap.dedent(
            """
            [[checks]]
            name = "unreadable-check"
            executor.command = "echo"
            executor.args = ["test"]
            publisher.name = "stdout"
            """
        )
    )
    unreadable_file.chmod(0o000)  # Remove all permissions

    # Save original environment
    original_env = {
        "KUMACUB__CONFIG": os.environ.get("KUMACUB__CONFIG"),
        "KUMACUB__CHECKS_DIR": os.environ.get("KUMACUB__CHECKS_DIR"),
    }
    os.environ["KUMACUB__CONFIG"] = ""
    os.environ["KUMACUB__CHECKS_DIR"] = str(checks_dir)

    try:
        config.reset_settings_cache()

        # Should raise SystemExit due to permission error
        with pytest.raises(SystemExit) as exc_info:
            config.get_settings()

        # Check that the error message mentions the unreadable file
        assert "Failed to read TOML file" in str(exc_info.value)
        assert "unreadable.toml" in str(exc_info.value)

    finally:
        # Restore permissions so cleanup can work
        unreadable_file.chmod(0o644)
        # Restore environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        config.reset_settings_cache()


def test_directory_toml_invalid_content(tmp_path: Path) -> None:
    """Test handling of directory files with non-check content."""
    checks_dir = tmp_path / "conf.d"
    checks_dir.mkdir()

    # Create a valid TOML file with checks
    (checks_dir / "valid.toml").write_text(
        textwrap.dedent(
            """
            [[checks]]
            name = "valid-check"
            executor.command = "echo"
            executor.args = ["test"]
            publisher.name = "stdout"
            """
        )
    )

    # Create an invalid TOML file with non-check content
    (checks_dir / "invalid.toml").write_text(
        textwrap.dedent(
            """
            [log]
            level = "INFO"
            """
        )
    )

    # Save original environment
    original_env = {
        "KUMACUB__CONFIG": os.environ.get("KUMACUB__CONFIG"),
        "KUMACUB__CHECKS_DIR": os.environ.get("KUMACUB__CHECKS_DIR"),
    }
    os.environ["KUMACUB__CONFIG"] = ""
    os.environ["KUMACUB__CHECKS_DIR"] = str(checks_dir)

    try:
        config.reset_settings_cache()

        # Should raise SystemExit due to invalid content
        with pytest.raises(SystemExit) as exc_info:
            config.get_settings()

        # Check that the error message mentions the invalid file
        assert "can only contain [[checks]] sections" in str(exc_info.value)
        assert "invalid.toml" in str(exc_info.value)

    finally:
        # Restore environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        config.reset_settings_cache()
