#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""KumaCub application services runner."""

import textwrap
import time
from typing import cast

from kumacub.domain import models
from kumacub.infrastructure import executors, parsers, publishers


class Runner:
    """Runner service.

    Needs:
    - executor
    - parser
    - translator
    - publisher

    """

    def __init__(
        self, executor: executors.ExecutorP, parser: parsers.ParserP, publisher: publishers.PublisherP
    ) -> None:
        """Initialize a Runner instance."""
        self._executor = executor
        self._parser = parser
        self._publisher = publisher
        self._start_time: float | None = None

    async def run(self, check: models.Check) -> None:
        """Execute a check and publish the result."""
        self._timer()
        executor_args = executors.ProcessExecutorArgs(
            id=check.name,
            command=check.executor.command,
            args=check.executor.args,
            env=check.executor.env,
        )
        executor_output = await self._executor.run(executor_args)
        executor_output = cast("executors.ProcessExecutorOutput", executor_output)
        parser_args = parsers.NagiosParserArgs(
            id=check.name,
            output=executor_output.stdout or executor_output.stderr,
            exit_code=executor_output.exit_code,
        )
        parser_output = self._parser.parse(parser_args)
        parser_output = cast("parsers.NagiosParserOutput", parser_output)
        max_msg_len = publishers.UptimeKumaPublishArgs.model_fields["msg"].metadata[0].max_length
        publisher_args = publishers.UptimeKumaPublishArgs(
            id=check.name,
            url=check.publisher.url,
            push_token=check.publisher.push_token,
            status="up" if parser_output.exit_code == 0 else "down",
            msg=textwrap.shorten(parser_output.service_output, width=max_msg_len, placeholder="..."),
            ping=self._timer(),
        )
        await self._publisher.publish(args=publisher_args)

    def _timer(self) -> float:
        """Return the elapsed time (in milliseconds) since the timer started and reset the timer."""
        result = (time.time() - self._start_time) * 1000 if self._start_time is not None else 0.0
        self._start_time = time.time()
        return result
