#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""FastAPI app for KumaCub.

Includes an application factory that allows tests to inject service registrars.
"""

from __future__ import annotations

import importlib.metadata
from typing import TYPE_CHECKING, Final, cast

import fastapi
import pydantic
import svcs
from fastapi.exceptions import RequestValidationError

from kumacub import api, config, logging_config, middleware
from kumacub.services import auth_svc, greeter_svc

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable

    from starlette.types import Lifespan


# Configure logging early so it applies in the uvicorn worker process as well
_log_settings = config.get_settings().log
logging_config.configure_logging(level=_log_settings.level, structured=_log_settings.structured)

OPENAPI_TAGS: Final[list[dict[str, str]]] = [
    {
        "name": "Auth",
        "description": "OAuth2 authentication: login with form data to get a JWT; use Bearer on protected routes.",
    },
    {"name": "Health", "description": "Application health checks."},
    # TODO: Update/remove the "Sample" tag once you replace sample endpoints with real ones.
    {
        "name": "Sample",
        "description": "Sample endpoints (e.g., Greeter) showing svcs DI, settings, and JWT.",
    },
]


def make_lifespan(
    register_services_fn: Callable[[svcs.Registry], None] | None = None,
) -> Lifespan[fastapi.FastAPI]:
    """Create a svcs-aware lifespan function.

    Args:
        register_services_fn: Optional callback to register service factories and health
            pings. If None, no services are registered by default.

    Returns:
        A FastAPI-compatible lifespan callable wrapped by svcs.

    Usage:
    ```python
    import svcs

    def registrar(registry: svcs.Registry) -> None:
        # Avoid resolving settings at import time; use container in factories.
        registry.register_factory(MyProto, make_my_service, ping=ping_my_service)

    app = create_app(register_services_fn=registrar)
    ```
    """

    @svcs.fastapi.lifespan
    async def _lifespan(_app: fastapi.FastAPI, registry: svcs.Registry) -> AsyncGenerator[dict[str, object]]:
        # Register settings into the container first so registrars can resolve it.
        registry.register_factory(config.Settings, config.get_settings)

        if register_services_fn is not None:
            # Allow tests to override default services.
            register_services_fn(registry)
        else:
            # Register default services with health pings.
            registry.register_factory(
                auth_svc.AuthSvcP,
                auth_svc.make_auth_svc,
                ping=auth_svc.ping_auth_svc,
            )
            # TODO: Remove sample Greeter registration and register your real services.
            registry.register_factory(
                greeter_svc.GreeterSvcP,
                greeter_svc.make_greeter_svc,
                ping=greeter_svc.ping_greeter_svc,
            )

        # Add initial state; it's copied to request.state.
        yield {"app": "kumacub"}

    return cast("Lifespan[fastapi.FastAPI]", _lifespan)


def create_app(
    register_services_fn: Callable[[svcs.Registry], None] | None = None,
) -> fastapi.FastAPI:
    """Create and configure the FastAPI application.

    Args:
        register_services_fn: Optional callback for tests to register service factories.

    Returns:
        The configured FastAPI application.

    Tip: In tests, pass a registrar that registers fakes to isolate endpoints
    from real dependencies.
    """
    service_name = "kumacub"
    package_name = service_name.replace("-", "_")
    app_ = fastapi.FastAPI(
        title=service_name,
        description=importlib.metadata.metadata(package_name).get("Summary", ""),
        version=importlib.metadata.version(package_name),
        openapi_tags=OPENAPI_TAGS,
        lifespan=make_lifespan(register_services_fn),
        swagger_ui_init_oauth={
            "clientId": "kumacub-swagger",
            "appName": service_name,
            "usePkceWithAuthorizationCodeGrant": True,
        },
    )

    app_.include_router(api.router)
    app_.add_middleware(lambda ap: middleware.RequestContextMiddleware(ap))

    # Map internal Pydantic validation errors to a concise JSON response.
    @app_.exception_handler(pydantic.ValidationError)
    async def _validation_error_handler(_request: fastapi.Request, exc: pydantic.ValidationError) -> fastapi.Response:
        return fastapi.responses.JSONResponse(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": "Invalid token or claims",
                "errors": exc.errors(),
            },
        )

    # Map FastAPI request validation errors to a concise JSON 422 response.
    @app_.exception_handler(RequestValidationError)
    async def _request_validation_error_handler(
        _request: fastapi.Request, exc: RequestValidationError
    ) -> fastapi.Response:
        return fastapi.responses.JSONResponse(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "detail": "Invalid request",
                "errors": exc.errors(),
            },
        )

    # Add additional exception handlers for our API endpoints.
    for endpoint in [api.v1.auth]:
        endpoint.add_exception_handlers(app_)

    # TODO: Remove this root redirect to interactive API docs in real projects.
    @app_.get("/", include_in_schema=False)
    async def _redirect_root() -> fastapi.responses.RedirectResponse:
        return fastapi.responses.RedirectResponse(url="/docs", status_code=307)

    return app_


app = create_app()
