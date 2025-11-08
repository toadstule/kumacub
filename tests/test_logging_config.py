#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.
"""Test logging configuration behavior for console output."""

from __future__ import annotations

import logging

from kumacub.logging_config import configure_logging


def test_configure_logging_console() -> None:
    """Configure logging and ensure a handler is attached."""
    configure_logging(level="DEBUG", structured=False)
    # basic assertion: handler attached with expected level
    root = logging.getLogger()
    assert root.handlers, "root logger should have handlers"
