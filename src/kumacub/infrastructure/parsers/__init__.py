#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Parsers for different check types."""

from typing import Protocol

import pydantic

from .nagios import NagiosParser

_REGISTRY = {"nagios": NagiosParser}


class ParserP(Protocol):
    """Protocol for converting raw outputs into structured models."""

    def parse(self, output: str, exit_code: int = 0) -> pydantic.BaseModel:
        """Parse raw process output into a structured model.

        Args:
            output: The raw output from the process
            exit_code: The exit code from the process (default: 0)

        Returns:
            A pydantic model containing the parsed data
        """


def get_parser(name: str) -> ParserP:
    """Construct a parser by name."""
    try:
        return _REGISTRY[name]()
    except KeyError as e:
        msg = f"Unknown parser: {name}"
        raise ValueError(msg) from e
