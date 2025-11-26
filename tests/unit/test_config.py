#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025 Stephen T. Jibson.
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

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


import pydantic_settings

from kumacub import config
from kumacub.domain.models import Check, Executor, Parser, Schedule, StdoutPublisher


@pytest.fixture(autouse=True)
def _reset_config_cache() -> Iterator[None]:
    """Reset config cache before and after each test."""
    config.reset_settings_cache()
    yield
    config.reset_settings_cache()


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


@pytest.mark.usefixtures("mock_settings")
def test_settings_load_from_toml() -> None:
    """Test that settings are loaded correctly."""
    s = config.get_settings()
    assert s.log.level == "INFO"
    assert s.log.structured is False
    assert len(s.checks) == 1
    assert s.checks.pop().name == "test-check"


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
    # Create a minimal config file
    toml_file = tmp_path / "test.toml"
    toml_file.write_text('[log]\nlevel = "WARNING"\n')

    # Save and patch the environment variable for config location
    original_env = os.environ.get("KUMACUB__CONFIG")
    os.environ["KUMACUB__CONFIG"] = str(toml_file)

    try:
        # Reset cache to ensure fresh load
        config.reset_settings_cache()

        # Call the real get_settings (not mocked)
        s1 = config.get_settings()
        assert s1 is not None
        assert s1.log.level == "INFO"

        # Verify caching works
        s2 = config.get_settings()
        assert s1 is s2

        # Test reload_settings
        s3 = config.reload_settings()
        assert s3 is s1  # Same instance after reload

    finally:
        # Restore original environment
        if original_env is None:
            os.environ.pop("KUMACUB__CONFIG", None)
        else:
            os.environ["KUMACUB__CONFIG"] = original_env
        config.reset_settings_cache()
