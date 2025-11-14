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
from typing import ClassVar

import pydantic
import structlog


class ProcessExecutorArgs(pydantic.BaseModel):
    """Process executor args."""

    id: str
    command: str
    args: list[str] = []
    env: dict[str, str] = {}


class ProcessExecutorOutput(pydantic.BaseModel):
    """Process executor output."""

    stdout: str
    stderr: str
    exit_code: int


class _ProcessExecutor:
    """Process executor."""

    name: ClassVar[str] = "process"

    @staticmethod
    async def run(args: ProcessExecutorArgs) -> ProcessExecutorOutput:
        """Run a check and return the result."""
        logger = structlog.get_logger().bind(id=args.id)
        logger.info("Running check")

        proc = await asyncio.create_subprocess_exec(
            args.command,
            *args.args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=args.env,
        )
        stdout_data, stderr_data = await proc.communicate()
        stdout = stdout_data.decode().strip()
        stderr = stderr_data.decode().strip()

        if proc.returncode != 0:
            logger.warning("Check failed", exit_code=proc.returncode)
        else:
            logger.info("Check completed", exit_code=proc.returncode)
        if stdout:
            logger.debug("Check output", stdout=stdout)
        if stderr:
            logger.warning("Check output", stderr=stderr)

        return ProcessExecutorOutput(stdout=stdout, stderr=stderr, exit_code=proc.returncode or 0)
