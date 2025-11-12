#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""KumaCub infrastructure publishers."""

from typing import Any, Protocol, TypeVar

import pydantic

from kumacub.infrastructure.publishers.uptime_kuma import UptimeKumaPublisher

TPublishArgs_contra = TypeVar("TPublishArgs_contra", bound=pydantic.BaseModel, contravariant=True)

_REGISTRY = {"uptime_kuma": UptimeKumaPublisher}


class PublisherP(Protocol[TPublishArgs_contra]):
    """Protocol for publishing data to external services."""

    async def publish(self, args: TPublishArgs_contra) -> None:
        """Publish data to the external service.

        Args:
            args: The data to publish, must be a pydantic BaseModel
        """


def get_publisher(name: str, *args: object, **kwargs: object) -> PublisherP[Any]:
    """Construct a publisher by name with provided constructor args."""
    try:
        _REGISTRY[name](*args, **kwargs)
    except KeyError as e:
        msg = f"Unknown publisher type: {name}"
        raise ValueError(msg) from e
