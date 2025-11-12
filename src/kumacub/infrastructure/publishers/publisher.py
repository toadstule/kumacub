#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Infrastructure publishers registry and base class."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, ClassVar

import structlog

if TYPE_CHECKING:
    import pydantic


# Base generic publisher that accepts a pydantic model as its argument type.
class Publisher[A: "pydantic.BaseModel"](abc.ABC):
    """Base publisher for sending results to external services."""

    _registry: ClassVar[dict[str, type[Publisher[Any]]]] = {}

    def __init__(self) -> None:
        """Initialize a Publisher instance."""
        self._logger = structlog.get_logger()

    def __init_subclass__(cls, publisher_type: str, **kwargs: object) -> None:
        """Register a publisher for a specific type."""
        super().__init_subclass__(**kwargs)
        cls._registry[publisher_type] = cls

    @classmethod
    def factory(cls, publisher_type: str) -> Publisher[Any]:
        """Return a publisher for a specific type."""
        try:
            return cls._registry[publisher_type]()
        except KeyError as e:
            msg = f"Unknown publisher type: {publisher_type}"
            raise ValueError(msg) from e

    @abc.abstractmethod
    async def publish(self, args: A) -> None:  # pragma: no cover
        """Publish a check result to the remote service."""
        raise NotImplementedError


def get_publisher(publisher_type: str) -> Publisher[Any]:
    """Return a publisher for a specific type."""
    return Publisher.factory(publisher_type)
