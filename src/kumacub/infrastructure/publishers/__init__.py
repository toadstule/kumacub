#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Publishers for different monitoring services."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Final, Protocol

from .uptime_kuma import UptimeKumaPublishArgs, _UptimeKumaPublisher

if TYPE_CHECKING:
    import pydantic

# Export all arg models.
__all__ = ["PublisherP", "UptimeKumaPublishArgs", "get_publisher"]

# Extend this to add new publishers.
_PUBLISHERS: Final[list[type[PublisherP]]] = [_UptimeKumaPublisher]  # type: ignore[list-item]

_REGISTRY: Final[dict[str, type[PublisherP]]] = {p.name: p for p in _PUBLISHERS}


class PublisherP(Protocol):
    """Protocol for publishing check results to external services."""

    name: ClassVar[str] = ""

    async def publish(self, args: pydantic.BaseModel) -> None:
        """Publish check results to the external service.

        Args:
            args: Publisher-specific arguments as a pydantic model.
        """


def get_publisher(name: str) -> PublisherP:
    """Construct a parser by name."""
    try:
        return _REGISTRY[name]()
    except KeyError as e:
        msg = f"Unknown publisher: {name}"
        raise ValueError(msg) from e
