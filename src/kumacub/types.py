#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.


"""KumaCub types."""

from typing import Literal

import pydantic


class Check(pydantic.BaseModel):
    """KumaCub Check."""

    name: str
    command: str
    args: list[str] = []
    env: dict[str, str] = {}


class CheckResult(pydantic.BaseModel):
    """KumaCub Check Result.

    Attributes:
        name: Name of the check
        exit_code: Exit code from the check
        service_state: Service state (OK, WARNING, CRITICAL, UNKNOWN)
        service_output: Main text output from the check
        service_performance_data: Space-separated performance data metrics
        long_service_output: Additional text output lines
    """

    name: str
    exit_code: int
    service_state: Literal["OK", "WARNING", "CRITICAL", "UNKNOWN"]
    service_output: str = ""
    service_performance_data: str = ""
    long_service_output: str = ""

    @classmethod
    def from_nagios_output(cls, name: str, exit_code: int, output: str) -> "CheckResult":
        """Create a CheckResult from Nagios-compatible plugin output."""
        state_map: dict[int, Literal["OK", "WARNING", "CRITICAL", "UNKNOWN"]] = {
            0: "OK",
            1: "WARNING",
            2: "CRITICAL",
            3: "UNKNOWN",
        }

        lines = [line.strip() for line in output.splitlines() if line.strip()]
        if not lines:
            return cls(
                name=name,
                exit_code=exit_code,
                service_state=state_map.get(exit_code, "UNKNOWN"),
                service_output="",
                service_performance_data="",
                long_service_output="",
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

        return cls(
            name=name,
            exit_code=exit_code,
            service_state=state_map.get(exit_code, "UNKNOWN"),
            service_output=text_output,
            service_performance_data=performance_data,
            long_service_output=long_service_output,
        )
