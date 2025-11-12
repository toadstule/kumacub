#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Executors for checks."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Final, Protocol

from .process_executor import _ProcessExecutor

if TYPE_CHECKING:
    from kumacub.domain import models

__all__ = ["ExecutorP", "get_executor"]

# Extend this to add new executors.
_EXECUTORS: Final[list[type[ExecutorP]]] = [_ProcessExecutor]

_REGISTRY: Final[dict[str, type[ExecutorP]]] = {p.name: p for p in _EXECUTORS}


class ExecutorP(Protocol):
    """Protocol for executing checks and returning results."""

    name: ClassVar[str] = ""

    async def run(self, check: models.Check) -> models.CheckResult:
        """Execute a check and return the result.

        Args:
            check: The check to execute

        Returns:
            The result of the check execution
        """


def get_executor(name: str) -> ExecutorP:
    """Construct an executor by name."""
    try:
        return _REGISTRY[name]()
    except KeyError as e:
        msg = f"Unknown executor: {name}"
        raise ValueError(msg) from e
