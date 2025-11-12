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

from typing import Final, Literal

import pydantic


class Result(pydantic.BaseModel):
    """Nagios-style check result."""

    service_state: Literal["OK", "WARNING", "CRITICAL", "UNKNOWN"]
    exit_code: int
    service_output: str
    long_service_output: str
    service_performance_data: str


class NagiosParser:
    """Nagios parser in infrastructure: raw parsing only."""

    _state_map: Final[dict[int, Literal["OK", "WARNING", "CRITICAL", "UNKNOWN"]]] = {
        0: "OK",
        1: "WARNING",
        2: "CRITICAL",
        3: "UNKNOWN",
    }

    def parse(self, exit_code: int, output: str) -> Result:
        """Parse the raw output into the parser-specific model."""
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        if not lines:
            return Result(
                service_state="UNKNOWN",
                exit_code=3,
                service_output="",
                long_service_output="",
                service_performance_data="",
            )

        first_line = lines.pop(0)
        text_output = first_line
        performance_data = ""

        if "|" in first_line:
            text_output, performance_data = (part.strip() for part in first_line.split("|", 1))

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

        performance_data = " ".join(filter(None, performance_data_parts))
        long_service_output = "\n".join(long_text_lines)

        return Result(
            service_state=self._state_map.get(exit_code, "UNKNOWN"),
            exit_code=exit_code,
            service_output=text_output,
            long_service_output=long_service_output,
            service_performance_data=performance_data,
        )
