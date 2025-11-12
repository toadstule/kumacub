#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Infrastructure parsers for raw check output parsing."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, ClassVar

import structlog

if TYPE_CHECKING:
    import pydantic


class Parser(abc.ABC):
    """Base parser for converting raw outputs into structured parser-specific models."""

    _registry: ClassVar[dict[str, type[Parser]]] = {}

    def __init__(self) -> None:
        """Initialize a Parser instance."""
        self._logger = structlog.get_logger()

    def __init_subclass__(cls, check_type: str, **kwargs: object) -> None:
        """Register a parser for a specific check type."""
        super().__init_subclass__(**kwargs)
        cls._registry[check_type] = cls

    @classmethod
    def factory(cls, check_type: str) -> Parser:
        """Return a parser for a specific check type."""
        try:
            return cls._registry[check_type]()
        except KeyError as e:
            msg = f"Unknown check type: {check_type}"
            raise ValueError(msg) from e

    @abc.abstractmethod
    def parse(self, exit_code: int, output: str) -> pydantic.BaseModel:
        """Parse raw process output into a structured model."""
        raise NotImplementedError  # pragma: no cover


def get_parser(check_type: str) -> Parser:
    """Return a parser for a specific check type."""
    return Parser.factory(check_type)
