#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.


"""KumaCub types."""

from __future__ import annotations

from typing import Protocol


class DepContainerP(Protocol):
    """Minimal protocol for the svcs dependency container used by the app.

    We only rely on ``get_abstract(Settings)`` in our code/tests, so this is the
    only method we declare for structural compatibility.

    Usage:
    - Under ``TYPE_CHECKING``, annotate a FastAPI param as ``DepContainerP``
      to help static typing when resolving multiple services.
    - At runtime use ``svcs.fastapi.DepContainer``.
    - When resolving different protocols from the same ``services`` param, prefer
      ``typing.cast(...)`` to narrow types for the call site.
    """

    async def aget_abstract(self, tp: object) -> object:
        """Return an instance for the requested abstract type."""

    def get_abstract(self, tp: object) -> object:
        """Return an instance for the requested abstract type."""


class HealthPingP(Protocol):
    """Minimal interface for a registered health ping."""

    name: str

    async def aping(self) -> None:
        """Run the ping, raising on failure."""


class HealthPingsP(Protocol):
    """Container interface exposing registered health pings.

    Services registered with ``ping=`` in the lifespan are surfaced by
    ``services.get_pings()`` and exercised by ``/api/v1/health/deep``.
    """

    def get_pings(self) -> list[HealthPingP]:
        """Return the list of registered pings."""
