#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Test configuration loading from TOML and environment variables."""

from __future__ import annotations

import textwrap
import typing
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from kumacub import config


@pytest.fixture(autouse=True)
def _reset_config_cache() -> typing.Iterator[None]:
    """Reset config cache before and after each test."""
    config.reset_settings_cache()
    yield
    config.reset_settings_cache()


@pytest.fixture
def config_toml_file(tmp_path: Path) -> typing.Iterator[Path]:
    """Create a temporary config TOML file and set toml_file in model_config."""
    toml = tmp_path / "cfg.toml"
    toml.write_text(
        textwrap.dedent(
            """
            service_name = "kumacub"
            [log]
            level = "DEBUG"
            structured = false
            """
        )
    )
    # Set the toml_file directly in model_config
    # Note: This is a workaround since CONFIG env var is read at class definition time
    original_toml_file = config.Settings.model_config.get("toml_file")
    config.Settings.model_config["toml_file"] = str(toml)

    yield toml

    # Restore original value
    if original_toml_file is not None:
        config.Settings.model_config["toml_file"] = original_toml_file
    else:
        config.Settings.model_config.pop("toml_file", None)


@pytest.mark.usefixtures("config_toml_file")
def test_settings_load_from_toml() -> None:
    """Test that settings are loaded from TOML file."""
    s = config.get_settings()

    assert s.service_name == "kumacub"
    assert s.log.level == "DEBUG"
    assert s.log.structured is False


@pytest.mark.usefixtures("config_toml_file")
def test_settings_env_overrides_toml(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that environment variables override TOML settings."""
    # First load from TOML
    s = config.get_settings()
    assert s.log.level == "DEBUG"

    # Override via env using monkeypatch (auto-cleanup)
    monkeypatch.setenv("KUMACUB__LOG__LEVEL", "WARNING")
    config.reload_settings()

    assert config.get_settings().log.level == "WARNING"


def test_settings_defaults_when_no_toml(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that settings use defaults when no TOML file exists."""
    # Point to non-existent file
    monkeypatch.setenv("CONFIG", "/nonexistent/config.toml")

    s = config.get_settings()

    assert s.service_name == "kumacub"
    assert s.log.level == "INFO"  # Default
    assert s.log.structured is True  # Default
    assert s.checks == []  # Default


def test_settings_cache_behavior() -> None:
    """Test that get_settings() returns cached instance."""
    s1 = config.get_settings()
    s2 = config.get_settings()

    assert s1 is s2  # Same instance


def test_reset_settings_cache_clears_cache() -> None:
    """Test that reset_settings_cache() clears the cache."""
    s1 = config.get_settings()

    config.reset_settings_cache()

    s2 = config.get_settings()
    assert s1 is not s2  # Different instances


def test_reload_settings_updates_in_place(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that reload_settings() updates existing instance."""
    s1 = config.get_settings()
    original_level = s1.log.level

    # Change environment
    new_level = "CRITICAL" if original_level != "CRITICAL" else "DEBUG"
    monkeypatch.setenv("KUMACUB__LOG__LEVEL", new_level)

    s2 = config.reload_settings()

    # Should be same instance but with updated values
    assert s1 is s2
    assert s2.log.level == new_level
