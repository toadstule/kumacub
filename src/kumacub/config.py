#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
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
from functools import lru_cache
from typing import Annotated, Literal

import pydantic
import pydantic_settings

from kumacub.domain import models  # noqa: TC001


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
        toml_file=os.environ.get("KUMACUB__CONFIG", "/etc/kumacub/config.toml"),
    )

    # App identity
    service_name: Annotated[str, pydantic.StringConstraints(strip_whitespace=True, min_length=1)] = "kumacub"

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
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            pydantic_settings.TomlConfigSettingsSource(settings_cls),
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
