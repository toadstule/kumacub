#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Test configuration for KumaCub template.

Provides a `test_app` fixture that creates an app with a test registrar, and
defaults auth to disabled (`AUTH__REQUIRED=false`). Individual tests can override
env via `monkeypatch.setenv`.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from kumacub import app as app_module
from tests.support import register

if TYPE_CHECKING:
    import fastapi


@pytest.fixture
def test_app() -> fastapi.FastAPI:
    """Return a FastAPI app instance with fake services registered.

    Usage:
    - Accept `test_app` in your test and use `TestClient(test_app)`.
    - Replace the registrar in `tests/support/register.py` with fakes for your services.
    """
    return app_module.create_app(register_services_fn=register.registrar_fn())


@pytest.fixture(autouse=True)
def _default_auth_and_clear_jwt_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests start with auth disabled and no JWT env noise.

    Individual tests can override via `monkeypatch.setenv("AUTH__REQUIRED", "true")`.
    JWT-related env vars are cleared to avoid cross-test flakiness.
    """
    monkeypatch.setenv("AUTH__REQUIRED", "false")
    for k in list(os.environ.keys()):
        if k.startswith("JWT__"):
            monkeypatch.delenv(k, raising=False)
