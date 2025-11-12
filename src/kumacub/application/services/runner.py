#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""KumaCub application services runner."""

from kumacub.application import result_translators
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
        self,
        executor: executors.ExecutorP,
        parser: parsers.ParserP,
        result_translator: result_translators.ResultTranslatorP,
        publisher: publishers.PublisherP,
    ) -> None:
        """Initialize a Runner instance."""
        self._executor = executor
        self._parser = parser
        self._result_translator = result_translator
        self._publisher = publisher

    async def run(self, check: models.Check) -> None:
        """Execute a check and publish the result."""
        raw_result = await self._executor.run(check=check)
        parsed_result = await self._parser.parse(raw_check_result)
        translated_result: self._result_translator.translate(parsed_result)
        await self._publisher.publish(args=translated_result)
