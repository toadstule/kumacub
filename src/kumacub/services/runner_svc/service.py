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

import structlog

from kumacub import types


class RunnerSvc:
    """Check runner service."""

    def __init__(self) -> None:
        """Initialize a RunnerSvc instance."""
        self._logger = structlog.get_logger()

    async def run(self, check: types.Check) -> types.CheckResult:
        """Run a check and return the result.

        Args:
            check: The check to run.

        Returns:
            CheckResult: The result of the check.
        """
        self._logger.debug("Running check: %s", check.name)

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
            return types.CheckResult.from_nagios_output(name=check.name, exit_code=exit_code, output=stdout)

        except Exception as e:
            self._logger.exception("Error running check %s", check.name)
            return types.CheckResult(
                name=check.name,
                exit_code=3,  # UNKNOWN
                service_state="UNKNOWN",
                service_output=f"Error executing check: {e!s}",
                long_service_output=f"Error details: {e!s}",
            )
