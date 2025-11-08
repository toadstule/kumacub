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

import os
import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from pathlib import Path

from kumacub import config


def test_settings_env_overrides_toml(tmp_path: Path) -> None:
    """Load from TOML and ensure env overrides take effect."""
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

    config.Settings.model_config["toml_file"] = str(toml)
    s = config.reload_settings()

    assert s.service_name == "kumacub"

    # Override via env
    os.environ["LOG__LEVEL"] = "WARNING"
    config.reload_settings()
    assert config.get_settings().log.level == "WARNING"

    # Clean up
    del os.environ["LOG__LEVEL"]
    config.reset_settings_cache()
