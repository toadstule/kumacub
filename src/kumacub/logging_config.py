#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Application-wide structured logging configuration using structlog.

This module configures stdlib logging to render JSON (or console) and
integrates structlog with contextvars for per-request context.
"""

from __future__ import annotations

import logging
import logging.config
from typing import Final

import structlog

DEFAULT_LEVEL: Final[str] = "INFO"


def configure_logging(level: str = DEFAULT_LEVEL, *, structured: bool = True) -> None:
    """Configure logging for the application.

    - Routes stdlib logging through structlog's ProcessorFormatter
    - Renders JSON by default (suitable for production/log aggregation)
    - Merges contextvars (request_id, method, path, etc.) into each event

    Args:
        level: Log level name (e.g., "DEBUG"). Defaults to INFO.
        structured: If True, render JSON; otherwise use a developer-friendly console renderer.

    Usage:
    - Call early in the HTTP entrypoint (see `entrypoints/http_server.py`).
    - Set `LOG__STRUCTURED=false` locally to switch to the console renderer.
    - Middleware (`RequestContextMiddleware`) injects request fields; they appear
      on every log line.
    """
    numeric_level = logging.getLevelNamesMapping().get(level.upper(), logging.INFO)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.PROCESS,
                structlog.processors.CallsiteParameter.THREAD,
            }
        ),
    ]

    # Choose renderer based on the "structured" option
    renderer: structlog.types.Processor
    if structured:
        shared_processors.append(structlog.processors.format_exc_info)
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    # Reset structlog to avoid cached loggers keeping stale processors
    structlog.reset_defaults()

    # Configure structlog so that its output is rendered by ProcessorFormatter below.
    structlog.configure(
        cache_logger_on_first_use=True,
        logger_factory=structlog.stdlib.LoggerFactory(),
        processors=[
            *shared_processors,  # type: ignore[list-item]
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
    )

    # ProcessorFormatter for stdlib logs (incl. uvicorn, fastapi, httpx, etc.)
    processor_formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,  # type: ignore[arg-type]
    )

    handler = logging.StreamHandler()
    handler.setFormatter(processor_formatter)
    handler.setLevel(numeric_level)

    # Apply to root logger and common libraries
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(numeric_level)

    for name in ("apscheduler", "httpx"):
        logging.getLogger(name).setLevel(numeric_level)
        logging.getLogger(name).propagate = True


__all__ = ["configure_logging"]
