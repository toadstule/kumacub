#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""KumaCub infrastructure executors."""

from typing import Protocol

from kumacub.domain import models

from .process_executor import ProcessExecutor

_REGISTRY = {"process": ProcessExecutor}


class ExecutorP(Protocol):
    """Protocol for executing checks and returning results."""

    async def run(self, check: models.Check) -> models.CheckResult:
        """Execute a check and return the result.

        Args:
            check: The check to execute

        Returns:
            The result of the check execution
        """


def get_parser(name: str) -> ExecutorP:
    """Construct a parser by name."""
    try:
        return _REGISTRY[name]()
    except KeyError as e:
        msg = f"Unknown parser: {name}"
        raise ValueError(msg) from e
