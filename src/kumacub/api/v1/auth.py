#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Authentication endpoints (v1).

Provides a Basic Auth login that returns a JWT for subsequent requests.

Usage:
- POST ``/api/v1/auth/login`` with HTTP Basic (``Authorization: Basic``) using
  credentials configured in ``Settings.auth``.
- Use the returned Bearer token (``Authorization: Bearer <token>``) on endpoints
  depending on ``require_jwt`` (see ``/api/v1/sample/protected``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, cast

import fastapi
import pydantic
from fastapi import security

from kumacub.api import http_auth
from kumacub.services import auth_svc

if TYPE_CHECKING:
    from kumacub.types import DepContainerP

else:
    import svcs

    DepContainerP = svcs.fastapi.DepContainer

router = fastapi.APIRouter(prefix="/auth", tags=["Auth"])

_basic = security.HTTPBasic()


class MeResponse(pydantic.BaseModel):
    """Response model for /me."""

    username: str


@router.post(
    "",
    summary="Login with OAuth2 form data, receive a JWT",
    description=(
        "Authenticates using OAuth2 password grant (form data) against AUTH__USERNAME and AUTH__PASSWORD. "
        "On success returns a JWT with claims: iss=kumacub, aud=kumacub, sub=<username>, exp."
    ),
    response_model=auth_svc.Token,
    responses={
        200: {"description": "Login successful", "model": auth_svc.Token},
        401: {"description": "Invalid credentials"},
        500: {"description": "JWT signing secret not configured"},
        503: {"description": "Authentication not configured"},
    },
)
def login(
    form_data: Annotated[fastapi.security.OAuth2PasswordRequestForm, fastapi.Depends()],
    services: DepContainerP,
) -> auth_svc.Token:
    """Authenticate via form data and return a signed JWT for subsequent requests.

    Args:
        form_data: User-provided credentials.
        services: DI container.
    """
    auth_service = cast("auth_svc.AuthSvcP", services.get_abstract(auth_svc.AuthSvcP))
    auth_service.validate_credentials(form_data.username, form_data.password)
    return auth_service.create_token(form_data.username)


@router.get(
    "/me",
    summary="Return information about the current user",
    description=(
        "Returns user information derived from the provided Bearer token. "
        "When auth.required is disabled, returns a placeholder identity for development."
    ),
    dependencies=[fastapi.Security(http_auth.oauth2_scheme)],
)
def me(claims: Annotated[auth_svc.Claims, fastapi.Depends(http_auth.require_jwt)]) -> MeResponse:
    """Return information about the current user."""
    return MeResponse(username=claims.sub)


@router.post(
    "/refresh",
    summary="Refresh a JWT",
    description="Validates the provided Bearer token and issues a new access token with a refreshed expiration.",
    response_model=auth_svc.Token,
    dependencies=[fastapi.Security(http_auth.oauth2_scheme)],
)
def refresh(
    services: DepContainerP,
    token: Annotated[str, fastapi.Security(http_auth.oauth2_scheme)],
) -> auth_svc.Token:
    """Refresh a JWT."""
    auth_service = cast("auth_svc.AuthSvcP", services.get_abstract(auth_svc.AuthSvcP))
    return auth_service.refresh_token(token)


@router.post(
    "/verify",
    summary="Verify a JWT",
    description="Verifies the provided JWT via Authorization: Bearer header. Returns {valid: true} on success.",
    dependencies=[fastapi.Security(http_auth.oauth2_scheme)],
    responses={
        200: {"description": "Token is valid", "content": {"application/json": {"example": {"valid": True}}}},
        401: {"description": "Invalid or missing token"},
        403: {"description": "Token issuer not allowed"},
    },
)
def verify(
    services: DepContainerP,
    token: Annotated[str, fastapi.Security(http_auth.oauth2_scheme)],
) -> dict[str, object]:
    """Verify a JWT."""
    auth_service = cast("auth_svc.AuthSvcP", services.get_abstract(auth_svc.AuthSvcP))
    auth_service.verify_token(token)
    return {"valid": True}


def add_exception_handlers(app: fastapi.FastAPI) -> None:
    """Install exception handlers for auth_svc exceptions."""

    @app.exception_handler(auth_svc.KumaCubAuthInvalidCredentialsError)
    async def _auth_invalid_credentials_handler(
        _request: fastapi.Request, exc: auth_svc.KumaCubAuthInvalidCredentialsError
    ) -> fastapi.Response:
        return fastapi.responses.JSONResponse(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)},
        )

    @app.exception_handler(auth_svc.KumaCubAuthInvalidTokenError)
    async def _auth_invalid_token_handler(
        _request: fastapi.Request, exc: auth_svc.KumaCubAuthInvalidTokenError
    ) -> fastapi.Response:
        return fastapi.responses.JSONResponse(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)},
        )

    @app.exception_handler(auth_svc.KumaCubAuthIssuerNotAllowedError)
    async def _auth_issuer_not_allowed_handler(
        _request: fastapi.Request, exc: auth_svc.KumaCubAuthIssuerNotAllowedError
    ) -> fastapi.Response:
        return fastapi.responses.JSONResponse(
            status_code=fastapi.status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc)},
        )

    @app.exception_handler(auth_svc.KumaCubAuthNotConfiguredError)
    async def _auth_not_configured_handler(
        _request: fastapi.Request, exc: auth_svc.KumaCubAuthNotConfiguredError
    ) -> fastapi.Response:
        return fastapi.responses.JSONResponse(
            status_code=fastapi.status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(exc)},
        )

    @app.exception_handler(auth_svc.KumaCubAuthSigningSecretNotConfiguredError)
    async def _auth_signing_secret_handler(
        _request: fastapi.Request, exc: auth_svc.KumaCubAuthSigningSecretNotConfiguredError
    ) -> fastapi.Response:
        return fastapi.responses.JSONResponse(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )
