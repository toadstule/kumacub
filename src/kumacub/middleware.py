#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""ASGI middleware to bind per-request context to structlog.

Adds fields like ``request_id``, ``method``, ``path``, ``client_ip``, ``user_agent``
into structlog's contextvars so all logs include them automatically.

Usage:
- Added in ``create_app()``: ``app.add_middleware(lambda ap: RequestContextMiddleware(ap))``
- Reads ``X-Request-Id`` header if present, otherwise generates a UUID and echoes it back.
- Access values via ``structlog.contextvars`` or ``request.state`` in handlers.
"""

from __future__ import annotations

import http
import time
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import structlog
from starlette import status

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send
else:  # pragma: no cover
    ASGIApp = Callable[..., Any]
    Message = dict[str, Any]
    Receive = Callable[[], Any]
    Scope = dict[str, Any]
    Send = Callable[[Any], Any]


class RequestContextMiddleware:
    """Bind a request-scoped context for structured logging (native ASGI).

    Emits an ``http_request`` log on response with duration and status code.
    5xx -> error, 4xx -> warning, otherwise info.
    """

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware with the downstream ASGI ``app``."""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process an ASGI request, bind contextvars, and emit access/error logs."""
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        method = scope.get("method", "").upper()
        path = scope.get("path", "")
        client_host = scope.get("client", (None,))[0] if scope.get("client") else None

        structlog.contextvars.clear_contextvars()
        request_id = headers.get("x-request-id") or str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=method,
            path=path,
            client_ip=client_host,
            user_agent=headers.get("user-agent"),
        )

        log = structlog.get_logger()
        start = time.perf_counter()

        status_code: int | None = None
        first_start_sent = False

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code, first_start_sent
            if message["type"] == "http.response.start":
                status_code = int(message.get("status", 200))
                headers_list = list(message.get("headers", []))
                if not any(k.lower() == b"x-request-id" for k, _ in headers_list):
                    headers_list.append((b"x-request-id", request_id.encode()))
                    message["headers"] = headers_list
                first_start_sent = True
            elif message["type"] == "http.response.body":
                more = message.get("more_body", False)
                if first_start_sent and not more:
                    sc = status_code or 200
                    _emit_access_log(log, start, sc)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            _emit_exception_log(log, start)
            raise
        finally:
            structlog.contextvars.clear_contextvars()


def _choose_log_fn(logger: structlog.stdlib.BoundLogger, status_code: int) -> Callable[..., Any]:
    try:
        http_status = http.HTTPStatus(status_code)
    except ValueError:
        return logger.error
    if http_status.is_server_error:
        return logger.error
    if http_status.is_client_error:
        return logger.warning
    return logger.info


def _emit_access_log(logger: structlog.stdlib.BoundLogger, start: float, sc: int) -> None:
    duration_ms = (time.perf_counter() - start) * 1000.0
    logger_fn = _choose_log_fn(logger, sc)
    logger_fn("http_request", status_code=sc, duration_ms=round(duration_ms, 2))


def _emit_exception_log(logger: structlog.stdlib.BoundLogger, start: float) -> None:
    duration_ms = (time.perf_counter() - start) * 1000.0
    logger.exception(
        "http_request",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        duration_ms=round(duration_ms, 2),
    )


__all__ = ["RequestContextMiddleware"]
