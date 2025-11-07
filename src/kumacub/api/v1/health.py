#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Health endpoints (v1).

How to add a ping
-----------------
Register your service with a ``ping=`` in the app lifespan. Example::

    import svcs

    def registrar(registry: svcs.Registry) -> None:
        registry.register_factory(MyProto, make_my_service, ping=ping_my_service)

The ping will appear in ``/api/v1/health/deep`` via ``services.get_pings()``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import fastapi
import pydantic
from starlette import status

if TYPE_CHECKING:
    from kumacub.types import HealthPingsP as DepContainerP
else:
    import svcs

    DepContainerP = svcs.fastapi.DepContainer


class HealthyResponse(pydantic.BaseModel):
    """Response model for /v1/healthy."""

    ok: list[str]
    failing: dict[str, str]


router = fastapi.APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="Liveness probe")
def health() -> dict[str, str]:
    """Return a simple OK payload for health checks."""
    return {"status": "ok"}


@router.get(
    "/deep",
    response_model=HealthyResponse,
    summary="Health check for external services",
    description=(
        "Pings all registered services via svcs health checks and reports status. "
        "This iterates `services.get_pings()`; services registered with a `ping=` function "
        "(e.g., the sample Greeter) are included automatically."
    ),
)
async def deep_health(services: DepContainerP) -> fastapi.responses.JSONResponse:
    """Return health of all registered external services.

    Each health ping's ``aping()`` is awaited; failures are collected in ``failing``
    and cause a 500 status. Successes are listed in ``ok``.
    """
    ok: list[str] = []
    failing: dict[str, str] = {}
    code = status.HTTP_200_OK

    for svc in services.get_pings():
        svc_short_name = svc.name.rsplit(".", 1)[-1].removesuffix("P")
        try:
            await svc.aping()  # works for sync & async pings
        except Exception as e:  # noqa: BLE001
            failing[svc_short_name] = repr(e)
            code = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            ok.append(svc_short_name)

    return fastapi.responses.JSONResponse(content={"ok": ok, "failing": failing}, status_code=code)
