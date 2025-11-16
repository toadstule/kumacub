#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Console entrypoint to run the FastAPI server for KumaCub.

Usage:
    $ kumacubd

Notes:
- Reads settings from `kumacub.config.get_settings()` (env > TOML). You can set
  `KUMACUB__CONFIG` to point at a TOML file (see `fs_overlay/etc/kumacub/config.toml`).
- Calls `configure_logging(level, structured)`; toggle console logs via
  `LOG__STRUCTURED=false` for local development.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import signal

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from kumacub import config
from kumacub.application.services import runner
from kumacub.infrastructure import executors, parsers, publishers
from kumacub.logging_config import configure_logging


def main() -> None:
    """KumaCub daemon."""
    settings = config.get_settings()
    configure_logging(level=settings.log.level, structured=settings.log.structured)
    asyncio.run(_main())


async def _main() -> None:
    """Async entrypoint for the KumaCub daemon."""
    settings = config.get_settings()
    logger = structlog.get_logger()
    loop = asyncio.get_running_loop()

    # Initialize scheduler and schedule all checks
    scheduler = AsyncIOScheduler(timezone=dt.UTC)
    _schedule_all_checks(scheduler, settings)

    # Setup signal handlers
    stop_event = asyncio.Event()

    # SIGINT/SIGTERM -> graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        # noinspection PyTypeChecker
        loop.add_signal_handler(sig, stop_event.set)

    # SIGHUP -> reload configuration
    if hasattr(signal, "SIGHUP"):

        def on_sighup() -> None:
            logger.info("Reloading configuration...")
            nonlocal settings
            settings = config.reload_settings()
            _schedule_all_checks(scheduler, settings)

        # noinspection PyTypeChecker
        loop.add_signal_handler(signal.SIGHUP, on_sighup)

    # Start the scheduler and wait for shutdown signal.
    scheduler.start()
    try:
        await stop_event.wait()
    finally:
        logger.info("Shutting down...")
        scheduler.shutdown()


def _schedule_all_checks(scheduler: AsyncIOScheduler, settings: config.Settings) -> None:
    """Schedule all checks from settings."""
    scheduler.remove_all_jobs()
    for index, check in enumerate(settings.checks):
        runner_ = runner.Runner(
            executor=executors.get_executor(check.executor.name),
            parser=parsers.get_parser(check.parser.name),
            publisher=publishers.get_publisher(check.publisher.name),
        )
        scheduler.add_job(
            func=runner_.run,
            trigger="interval",
            seconds=check.schedule.interval,
            kwargs={"check": check},
            id=f"check:{check.name}",
            next_run_time=dt.datetime.now(tz=dt.UTC) + dt.timedelta(seconds=index * 2),
        )


if __name__ == "__main__":  # pragma: no cover
    main()
