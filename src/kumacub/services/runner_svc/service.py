#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Check runner service."""

import asyncio
import time

import structlog

from kumacub import types
from kumacub.library import parsers


class RunnerSvc:
    """Check runner service."""

    def __init__(self) -> None:
        """Initialize a RunnerSvc instance."""
        self._logger = structlog.get_logger()
        self._start_time: float | None = None

    async def run(self, check: types.Check) -> types.CheckResult:
        """Run a check and return the result.

        Args:
            check: The check to run.

        Returns:
            The result of the check.
        """
        self._logger.info("Running check: %s", check.name)

        self._timer()
        try:
            proc = await asyncio.create_subprocess_exec(
                check.command,
                *check.args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={"PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", **check.env},
            )
            stdout_data, stderr_data = await proc.communicate()
            stdout = stdout_data.decode().strip()
            stderr = stderr_data.decode().strip()

            self._logger.debug("Check %s completed with exit code %s", check.name, proc.returncode)
            if stdout:
                self._logger.debug("Check %s stdout: %s", check.name, stdout)
            if stderr:
                self._logger.warning("Check %s stderr: %s", check.name, stderr)

            # Determine service state from exit code
            exit_code = proc.returncode or 0  # Default to 0 if None
            parser = parsers.Parser.factory(check_type=check.type)
            result = parser.map(check_result=parser.parse(exit_code=exit_code, output=stdout))
            result.ping = self._timer()

        except Exception as e:
            self._logger.exception("Error running check %s", check.name)
            return types.CheckResult(
                status="down",
                msg=f"Error executing check: {e!s}",
                ping=self._timer(),
            )

        return result

    def _timer(self) -> float:
        """Return the elapsed time (in milliseconds) since the timer started and reset the timer."""
        result = (time.time() - self._start_time) * 1000 if self._start_time is not None else 0.0
        self._start_time = time.time()
        return result
