#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025-2026 Stephen T. Jibson.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Application settings for KumaCub.

Uses Pydantic v2 and pydantic-settings. See README for details.
"""

from __future__ import annotations

import os
import pathlib
import tomllib
from functools import lru_cache
from typing import Any, Literal

import pydantic
import pydantic_settings

from kumacub.domain import models  # noqa: TC001


class _DirectoryTomlConfigSettingsSource(pydantic_settings.PydanticBaseSettingsSource):
    def __init__(
        self,
        settings_cls: type[pydantic_settings.BaseSettings],
        main_toml_file: str | None = None,
        checks_toml_dir: str | None = None,
    ) -> None:
        super().__init__(settings_cls)
        self.main_toml_file = pathlib.Path(main_toml_file) if main_toml_file else None
        self.checks_toml_dir = pathlib.Path(checks_toml_dir) if checks_toml_dir else None

    def get_field_value(self, field: pydantic.fields.FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        del field  # Unused.  # pragma: no cover
        return None, field_name, False  # pragma: no cover

    def __call__(self) -> dict[str, Any]:
        non_check_data = {}
        all_checks = []
        all_toml_files: list[pathlib.Path] = []

        if self.checks_toml_dir is not None and self.checks_toml_dir.is_dir():
            all_toml_files.extend(sorted(self.checks_toml_dir.glob("*.toml")))
        if self.main_toml_file is not None and self.main_toml_file.is_file():
            all_toml_files.append(self.main_toml_file)

        for toml_file in all_toml_files:
            try:
                with toml_file.open("rb") as f:
                    data = tomllib.load(f)
            except OSError as e:
                # If any file can't be read, abort with clear error.
                msg = f"Failed to read TOML file {toml_file}: {e}"
                raise SystemExit(msg) from e
            except tomllib.TOMLDecodeError as e:
                # Invalid TOML should cause configuration to fail.
                msg = f"Invalid TOML in {toml_file}: {e}"
                raise SystemExit(msg) from e

            # Extract checks if present
            if "checks" in data:
                all_checks.extend(data["checks"])
                del data["checks"]  # Remove from data to handle separately.

            if toml_file == self.main_toml_file:
                non_check_data = data
            elif data:
                msg = f"{toml_file} can only contain [[checks]] sections"
                raise SystemExit(msg)

        if not all_checks:
            msg = "No checks found in configuration"
            raise SystemExit(msg)

        non_check_data["checks"] = all_checks
        return non_check_data


class LogSettings(pydantic.BaseModel):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    structured: bool = True


class Settings(pydantic_settings.BaseSettings):
    """Service configuration loaded automatically from environment variables."""

    # pydantic-settings configuration
    model_config = pydantic_settings.SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="KUMACUB__",
        extra="ignore",
    )

    # Checks configuration
    checks: list[models.Check] = []

    # Logging configuration
    log: LogSettings = LogSettings()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[pydantic_settings.BaseSettings],
        init_settings: pydantic_settings.PydanticBaseSettingsSource,
        env_settings: pydantic_settings.PydanticBaseSettingsSource,
        dotenv_settings: pydantic_settings.PydanticBaseSettingsSource,
        file_secret_settings: pydantic_settings.PydanticBaseSettingsSource,
    ) -> tuple[pydantic_settings.PydanticBaseSettingsSource, ...]:
        """Add TOML file source and prioritize: env > TOML > init > .env > secrets."""
        main_toml_file = os.environ.get("KUMACUB__CONFIG", "/etc/kumacub/config.toml")
        checks_toml_dir = os.environ.get("KUMACUB__CHECKS_DIR", "/etc/kumacub/checks.d")
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            _DirectoryTomlConfigSettingsSource(
                settings_cls, main_toml_file=main_toml_file, checks_toml_dir=checks_toml_dir
            ),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return current settings.

    Cached via lru_cache(maxsize=1) for efficiency. In tests (or when
    environment variables change), call `reset_settings_cache()` to refresh
    values.
    """
    return Settings()


def reload_settings() -> Settings:
    """Reload settings in-place from all configured sources and return them.

    This re-calls `__init__()` on the cached singleton returned by `get_settings()`
    so changes to environment variables or `Settings.model_config['toml_file']`
    take effect without clearing the cache or re-importing modules.
    """
    s = get_settings()
    # Pydantic recommends in-place reloading via __init__(); mypy flags this as unsound.
    s.__init__()  # type: ignore[misc]
    return s


def reset_settings_cache() -> None:
    """Reset cached settings (useful in tests when env changes)."""
    get_settings.cache_clear()
