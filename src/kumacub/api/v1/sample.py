#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Sample endpoints (v1) — replace with your own routes.

# TODO: This provides sample endpoints for demonstration. Replace/remove for your real project.

Demonstrates:
- ``/sample/echo`` — trivial echo
- ``/sample/error`` — triggers an exception to exercise middleware logging
- ``/sample/ping`` — public liveness
- ``/sample/protected`` — JWT-protected endpoint using ``require_jwt``
- ``/sample/setting`` — resolves ``Settings`` via svcs DI
- ``/sample/greet`` — resolves a sample service (``GreeterSvcP``) via svcs DI
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, cast

import fastapi

from kumacub import config
from kumacub.api import http_auth
from kumacub.services import auth_svc, greeter_svc

if TYPE_CHECKING:
    from kumacub.types import DepContainerP

else:
    import svcs

    DepContainerP = svcs.fastapi.DepContainer


router = fastapi.APIRouter(prefix="/sample", tags=["Sample"])


@router.get("/echo", summary="Echo a message")
def echo(msg: str = "hello") -> dict[str, str]:
    """Echo the provided ``msg`` query parameter."""
    return {"message": msg}


@router.get("/error", summary="Trigger an error (for middleware logging)")
def force_error() -> None:  # pragma: no cover - optional, used to demo exception logging
    """Raise an intentional error to demonstrate exception logging."""
    raise RuntimeError


@router.get("/ping", summary="Public ping")
def ping() -> dict[str, str]:
    """Public, unprotected endpoint for quick checks."""
    return {"message": "pong"}


@router.get("/protected", summary="Protected example")
async def protected(
    claims: Annotated[auth_svc.Claims, fastapi.Depends(http_auth.require_jwt)],
) -> dict[str, str | None]:
    """Require a valid JWT when ``auth.required=true`` and return a hello message."""
    return {"message": "hello", "sub": claims.sub if claims else None}


@router.get("/setting", summary="Using DI settings example")
async def service_name(services: DepContainerP) -> dict[str, str]:
    """Return the value of a setting resolved from the DI container.

    This demonstrates retrieving ``config.Settings`` via svcs in endpoint code.
    """
    settings = cast("config.Settings", services.get_abstract(config.Settings))
    return {"service-name": settings.service_name}


@router.get("/greet", summary="Greeter service example")
async def greet(services: DepContainerP, name: str = "World") -> dict[str, str]:
    """Use the Greeter service via DI to return a greeting.

    Resolves ``GreeterSvcP`` from svcs. The greeter is registered by default in
    ``kumacub.app.make_lifespan()`` and is configurable via ``Settings.greeter.prefix``.

    Example:
    ```bash
    curl 'http://127.0.0.1:8000/api/v1/sample/greet?name=Alice'
    # {"message": "hello, Alice from <service_name>"}
    ```
    """
    greeter = cast("greeter_svc.GreeterSvcP", services.get_abstract(greeter_svc.GreeterSvcP))
    return {"message": greeter.greet(name)}
