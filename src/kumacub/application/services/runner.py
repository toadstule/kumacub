#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""KumaCub application services runner."""

from kumacub.domain import models
from kumacub.infrastructure import executors, publishers
from kumacub.infrastructure.publishers.uptime_kuma import UptimeKumaPublishArgs


class Runner:
    """Runner service."""

    def __init__(self, kuma_client: publishers.PublisherP, process_executor: executors.ExecutorP) -> None:
        """Initialize a Runner instance."""
        self._kuma_client = kuma_client
        self._process_executor = process_executor

    async def run(self, check: models.Check) -> models.CheckResult:
        """Run a check and return the result."""
        return await self._process_executor.run(check=check)

    async def push(self, push_token: str, check_result: models.CheckResult) -> None:
        """Push a check result to Uptime Kuma.

        Args:
            push_token: The Uptime Kuma push token for this monitor.
            check_result: The result produced by running the check.

        Returns:
            PushResponse: Response from Uptime Kuma.
        """
        params = UptimeKumaPublishArgs(
            url="http://localhost:3001",
            push_token=push_token,
            status=check_result.status,
            msg=check_result.msg,
            ping=check_result.ping,
        )
        return await self._kuma_client.publish(args=params)
