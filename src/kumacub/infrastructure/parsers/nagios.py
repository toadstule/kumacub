#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Nagios parser in infrastructure: raw parsing only."""

from __future__ import annotations

from typing import ClassVar, Final, Literal

import pydantic
import structlog


class NagiosParserArgs(pydantic.BaseModel):
    """Nagios-style check args."""

    id: str
    exit_code: int
    output: str


class NagiosParserOutput(pydantic.BaseModel):
    """Nagios-style check output."""

    service_state: Literal["OK", "WARNING", "CRITICAL", "UNKNOWN"]
    exit_code: int
    service_output: str
    long_service_output: str
    service_performance_data: str


class _NagiosParser:
    """Output parser for Nagios-compatible checks."""

    name: ClassVar[str] = "nagios"

    _STATE_MAP: Final[dict[int, Literal["OK", "WARNING", "CRITICAL", "UNKNOWN"]]] = {
        0: "OK",
        1: "WARNING",
        2: "CRITICAL",
        3: "UNKNOWN",
    }

    def parse(self, args: NagiosParserArgs) -> NagiosParserOutput:
        """Parse the raw output into the parser-specific model."""
        logger = structlog.get_logger().bind(id=args.id)
        service_output = ""
        long_service_output = ""
        service_performance_data = ""

        lines = [line.strip() for line in args.output.splitlines() if line.strip()]
        if lines:
            performance_data = ""
            service_output = lines.pop(0)

            if "|" in service_output:
                service_output, performance_data = (part.strip() for part in service_output.split("|", 1))

            long_text_lines: list[str] = []
            performance_data_parts: list[str] = []
            in_performance_data = False

            if performance_data:
                performance_data_parts.append(performance_data)

            for line in lines:
                if "|" in line:
                    text_part, perf_part = (part.strip() for part in line.split("|", 1))
                    if text_part:
                        long_text_lines.append(text_part)
                    performance_data_parts.append(perf_part)
                    in_performance_data = True
                elif in_performance_data and line and not line.startswith((" ", "\t")):
                    performance_data_parts.append(line)
                else:
                    long_text_lines.append(line)
                    in_performance_data = False

            service_performance_data = " ".join(filter(None, performance_data_parts))
            long_service_output = "\n".join(long_text_lines)

        logger.debug("Parsed Nagios output", exit_code=args.exit_code, service_output=service_output)
        return NagiosParserOutput(
            service_state=self._STATE_MAP.get(args.exit_code, "UNKNOWN"),
            exit_code=args.exit_code,
            service_output=service_output,
            long_service_output=long_service_output,
            service_performance_data=service_performance_data,
        )
