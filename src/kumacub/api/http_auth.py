#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""FastAPI dependencies for HTTP authentication (Bearer scheme and JWT requirement)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, cast

import fastapi
from fastapi import security

from kumacub.services import auth_svc

if TYPE_CHECKING:
    from kumacub.types import DepContainerP

else:
    import svcs

    DepContainerP = svcs.fastapi.DepContainer


# Expose Basic and Bearer security schemes for OpenAPI.
oauth2_scheme = security.OAuth2PasswordBearer(tokenUrl="/api/v1/auth", auto_error=False)


async def require_jwt(
    services: DepContainerP,
    token: Annotated[str, fastapi.Security(oauth2_scheme)],
) -> auth_svc.Claims:
    """Require and validate a JWT provided via OAuth2 Bearer token.

    This dependency uses ``OAuth2PasswordBearer`` to read the access token from the
    ``Authorization: Bearer <token>`` header (with ``auto_error=False``). The raw token is
    passed to the auth service which returns validated claims, raises a domain error, or
    returns ``None`` when authentication is disabled.

    Args:
        services: Dependency injection container used to resolve ``AuthSvc``.
        token: The bearer token extracted by ``oauth2_scheme``. Will be an empty value when
            the header is missing because the scheme uses ``auto_error=False``.

    Returns:
        Claims: When authentication is enabled and the token is valid.
        None: When authentication is disabled (``settings.auth.required == False``).

    Raises:
        KumaCubAuthInvalidTokenError: Token is missing/empty or verification fails while auth is required.
        KumaCubAuthIssuerNotAllowedError: Token issuer does not match the configured service name.
        KumaCubAuthSigningSecretNotConfiguredError: Signing secret is not configured.

    HTTP mapping:
        These domain exceptions are mapped to HTTP responses by the exception handlers
        installed from ``kumacub.api.v1.auth.add_exception_handlers``:
        - Invalid token -> 401
        - Issuer not allowed -> 403
        - Signing secret not configured -> 500

    Example:
        Protect an endpoint and access the validated claims when auth is enabled. When
        auth is disabled, ``claims`` will be ``None`` and the endpoint proceeds.

        ```python
        @router.get("/me")
        def me(claims: Annotated[auth_svc.Claims, fastapi.Depends(http_auth.require_jwt)]) -> dict[str,str]:
            return {"sub": claims.sub}
        ```
    """
    auth_service = cast("auth_svc.AuthSvcP", services.get_abstract(auth_svc.AuthSvcP))
    return auth_service.extract_claims(token)
