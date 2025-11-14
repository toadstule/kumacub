#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Parsers for different check types."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Final, Protocol

from .nagios import NagiosParserArgs, NagiosParserOutput, _NagiosParser

if TYPE_CHECKING:
    import pydantic


# Export all args and output models.
__all__ = ["NagiosParserArgs", "NagiosParserOutput", "ParserP", "get_parser"]


# Extend this to add new parsers.
_PARSERS: Final[list[type[ParserP]]] = [_NagiosParser]  # type: ignore[list-item]

_REGISTRY: Final[dict[str, type[ParserP]]] = {p.name: p for p in _PARSERS}


class ParserP(Protocol):
    """Protocol for converting raw outputs into structured models."""

    name: ClassVar[str]

    def parse(self, args: pydantic.BaseModel) -> pydantic.BaseModel:
        """Parse raw process output into a structured model."""


def get_parser(name: str) -> ParserP:
    """Construct a parser by name."""
    try:
        return _REGISTRY[name]()
    except KeyError as e:
        msg = f"Unknown parser: {name}"
        raise ValueError(msg) from e
