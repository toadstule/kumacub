#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.
"""KumaCub domain protocols."""

from typing import Protocol

from kumacub.domain import models


class CheckExecutor(Protocol):
    """Check executor protocol."""

    async def run(self, check: models.Check) -> models.CheckResult:
        """Run a check and return the result."""


class MonitorClient(Protocol):
    """Monitor client protocol."""

    async def push(self, result: models.CheckResult, check: models.Check) -> None:
        """Push a check result to the monitor."""
