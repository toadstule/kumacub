#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""KumaCub daemon for running scheduled checks."""

import asyncio
import datetime as dt
import signal

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from kumacub import config
from kumacub.application.services import runner
from kumacub.infrastructure import executors, parsers, publishers


class KumaCubDaemon:
    """Main daemon class for KumaCub."""

    def __init__(self) -> None:
        """Initialize the KumaCub daemon."""
        self._logger = structlog.get_logger()
        self._scheduler = AsyncIOScheduler()
        self._settings = config.get_settings()
        self._stop_event = asyncio.Event()

    def run(self) -> None:
        """Run the KumaCub daemon."""
        asyncio.run(self._run())

    def _schedule_all_checks(self) -> None:
        """Schedule all checks from settings."""
        self._scheduler.remove_all_jobs()
        for index, check in enumerate(self._settings.checks):
            runner_ = runner.Runner(
                executor=executors.get_executor(check.executor.name),
                parser=parsers.get_parser(check.parser.name),
                publisher=publishers.get_publisher(check.publisher.name),
            )
            self._scheduler.add_job(
                func=runner_.run,
                trigger="interval",
                seconds=check.schedule.interval,
                kwargs={"check": check},
                id=f"check:{check.name}",
                next_run_time=dt.datetime.now(dt.UTC) + dt.timedelta(seconds=index * 2),
            )

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown and reload."""
        loop = asyncio.get_running_loop()

        # SIGINT/SIGTERM -> graceful shutdown
        for sig in (signal.SIGINT, signal.SIGTERM):
            # noinspection PyTypeChecker
            loop.add_signal_handler(sig, self._stop_event.set)

        # SIGHUP -> reload configuration
        if hasattr(signal, "SIGHUP"):

            def on_sighup() -> None:
                self._logger.info("Reloading configuration...")
                self._settings = config.reload_settings()
                self._schedule_all_checks()

            # noinspection PyTypeChecker
            loop.add_signal_handler(signal.SIGHUP, on_sighup)

    async def _run(self) -> None:
        """Run the KumaCub daemon."""
        self._schedule_all_checks()
        self._setup_signal_handlers()
        self._scheduler.start()

        try:
            await self._stop_event.wait()
        finally:
            self._logger.info("Shutting down...")
            if self._scheduler:
                self._scheduler.shutdown()
