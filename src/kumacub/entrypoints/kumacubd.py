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
  `CONFIG` to point at a TOML file (see `fs_overlay/etc/kumacub/config.toml`).
- Calls `configure_logging(level, structured)`; toggle console logs via
  `LOG__STRUCTURED=false` for local development.
"""

from __future__ import annotations

import asyncio
import os
import signal

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from kumacub import config
from kumacub.application.services import runner
from kumacub.infrastructure.executors.process_executor import ProcessExecutor
from kumacub.infrastructure.publishers.kuma_publisher import KumaClient
from kumacub.logging_config import configure_logging


def main() -> None:
    """KumaCub daemon."""
    settings = config.get_settings()
    configure_logging(level=settings.log.level, structured=settings.log.structured)
    asyncio.run(_main())


async def _main() -> None:
    """Async entrypoint for the KumaCub daemon."""
    settings = config.get_settings()

    # Graceful shutdown using signals
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        # noinspection PyTypeChecker
        loop.add_signal_handler(sig, stop_event.set)

    # Wire infrastructure
    kuma_url = os.environ.get("UPTIME_KUMA_URL", "http://localhost:3001")
    kuma_client = KumaClient(url=kuma_url)
    process_executor = ProcessExecutor()
    runner_ = runner.Runner(kuma_client=kuma_client, process_executor=process_executor)

    scheduler = AsyncIOScheduler()
    scheduler.start()
    # Keep references to background tasks created from signal handlers
    background_tasks: set[asyncio.Task[None]] = set()

    def schedule_checks(current_settings: config.Settings) -> None:
        for check in current_settings.checks:
            job_id = f"check:{check.name}"
            scheduler.add_job(
                func=runner_.run,
                trigger="interval",
                seconds=check.interval,
                kwargs={"check": check},
                id=job_id,
                replace_existing=True,
            )

    # Initial scheduling
    schedule_checks(settings)

    async def reload_and_reschedule() -> None:
        new_settings = config.reload_settings()
        # Build target job map
        target_jobs = {f"check:{c.name}": c for c in new_settings.checks}
        existing_jobs = {j.id: j for j in scheduler.get_jobs()}

        # Add or update jobs
        for job_id, check in target_jobs.items():
            if job_id in existing_jobs:
                # Reschedule interval in case it changed
                scheduler.reschedule_job(job_id=job_id, trigger="interval", seconds=check.interval)
            else:
                scheduler.add_job(
                    func=runner_.run,
                    trigger="interval",
                    seconds=check.interval,
                    kwargs={"check": check},
                    id=job_id,
                )

        # Remove jobs that no longer exist
        for job_id in set(existing_jobs.keys()) - set(target_jobs.keys()):
            scheduler.remove_job(job_id)

    # SIGHUP -> reload configuration and reschedule checks
    def on_sighup() -> None:
        task = asyncio.create_task(reload_and_reschedule())
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    if hasattr(signal, "SIGHUP"):
        # noinspection PyTypeChecker
        loop.add_signal_handler(signal.SIGHUP, on_sighup)

    try:
        await stop_event.wait()
    finally:
        scheduler.shutdown()  # Handle graceful shutdown


if __name__ == "__main__":  # pragma: no cover
    main()
