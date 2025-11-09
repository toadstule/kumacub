#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Result parsers."""

from __future__ import annotations

import abc
from typing import ClassVar, Final, Literal, cast

import pydantic
import structlog

from kumacub import types


class Parser(abc.ABC):
    """Parser Base class."""

    _registry: ClassVar[dict[str, type[Parser]]] = {}

    def __init__(self) -> None:
        """Initialize a ParserSvc instance."""
        self._logger = structlog.get_logger()

    def __init_subclass__(cls, check_type: str, **kwargs: object) -> None:
        """Register a parser for a specific check type."""
        super().__init_subclass__(**kwargs)
        cls._registry[check_type] = cls

    @classmethod
    def factory(cls, check_type: str) -> Parser:
        """Get a parser for a specific check type."""
        try:
            return cls._registry[check_type]()
        except KeyError as e:
            msg = f"Unknown check type: {check_type}"
            raise ValueError(msg) from e

    @abc.abstractmethod
    def map(self, check_result: pydantic.BaseModel) -> types.CheckResult:
        """Map a local check result to an Uptime Kuma check result."""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    def parse(self, exit_code: int, output: str) -> pydantic.BaseModel:
        """Parse the output of a check."""
        raise NotImplementedError  # pragma: no cover


class NagiosParser(Parser, check_type="nagios"):
    """Nagios-compatible check result parser."""

    class Result(pydantic.BaseModel):
        """Nagios-compatible check result."""

        service_state: Literal["OK", "WARNING", "CRITICAL", "UNKNOWN"]
        exit_code: int
        service_output: str
        long_service_output: str
        service_performance_data: str

    _state_map: Final[dict[int, Literal["OK", "WARNING", "CRITICAL", "UNKNOWN"]]] = {
        0: "OK",
        1: "WARNING",
        2: "CRITICAL",
        3: "UNKNOWN",
    }

    def map(self, check_result: pydantic.BaseModel) -> types.CheckResult:
        """Map a local check result to an Uptime Kuma check result."""
        check_result = cast("NagiosParser.Result", check_result)
        return types.CheckResult(
            status="up" if check_result.exit_code == 0 else "down",
            msg=check_result.service_output,
        )

    def parse(self, exit_code: int, output: str) -> NagiosParser.Result:
        """Parse Nagios-compatible check result."""
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        if not lines:
            return self.Result(
                service_state="UNKNOWN",
                exit_code=3,
                service_output="",
                long_service_output="",
                service_performance_data="",
            )

        # First line contains text output and optional performance data
        first_line = lines.pop(0)
        text_output = first_line
        performance_data = ""

        # Check for performance data in first line
        if "|" in first_line:
            text_output, performance_data = (part.strip() for part in first_line.split("|", 1))

        # Process remaining lines
        long_text_lines = []
        performance_data_parts = []
        in_performance_data = False

        if performance_data:
            performance_data_parts.append(performance_data)

        for line in lines:
            if "|" in line:
                # Split line into text and performance data parts.
                text_part, perf_part = (part.strip() for part in line.split("|", 1))
                if text_part:  # Only add to long text if there's actual text.
                    long_text_lines.append(text_part)
                performance_data_parts.append(perf_part)
                in_performance_data = True
            elif in_performance_data and line and not line.startswith((" ", "\t")):
                # If we're in a performance data block and the line doesn't start with whitespace,
                # treat it as a continuation of performance data.
                performance_data_parts.append(line)
            else:
                # If line has no pipe, and we're not in a performance data block, it's part of the long text output.
                long_text_lines.append(line)
                in_performance_data = False

        # Combine all performance data parts with spaces
        performance_data = " ".join(filter(None, performance_data_parts))
        long_service_output = "\n".join(long_text_lines)

        return self.Result(
            service_state=self._state_map.get(exit_code, "UNKNOWN"),
            exit_code=exit_code,
            service_output=text_output,
            long_service_output=long_service_output,
            service_performance_data=performance_data,
        )
