#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Process executor."""

import asyncio
import time

import structlog

import kumacub.application.result_translators as app_translators
import kumacub.infrastructure.parsers as infra_parsers
from kumacub.domain import models


class ProcessExecutor:
    """Process executor."""

    def __init__(self) -> None:
        """Initialize a ProcessExecutor instance."""
        self._logger = structlog.get_logger()
        self._start_time: float | None = None

    async def run(self, check: models.Check) -> models.CheckResult:
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
                env=check.env,
            )
            stdout_data, stderr_data = await proc.communicate()
            stdout = stdout_data.decode().strip()
            stderr = stderr_data.decode().strip()

            if proc.returncode != 0:
                self._logger.warning("Check %s failed with exit code %s", check.name, proc.returncode)
            else:
                self._logger.info("Check %s completed with exit code %s", check.name, proc.returncode)
            if stdout:
                self._logger.debug("Check %s stdout: %s", check.name, stdout)
            if stderr:
                self._logger.warning("Check %s stderr: %s", check.name, stderr)

            # Parse raw output (infrastructure) then map to domain (application)
            exit_code = proc.returncode or 0  # Default to 0 if None
            parser = infra_parsers.get_parser(check_type=check.type)
            parsed = parser.parse(exit_code=exit_code, output=stdout)
            result = app_translators.translate(check_type=check.type, parsed=parsed)
            result.ping = self._timer()

        except Exception as e:
            self._logger.exception("Error running check %s", check.name)
            return models.CheckResult(
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
