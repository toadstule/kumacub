#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Authentication service: protocol, implementation, factory, and ping.

Notes:
- Registered by default in `kumacub.app.make_lifespan()` when no custom registrar is provided.
- Encapsulates JWT creation, validation, and token management logic.
- Overridable in tests/dev by passing a custom ``register_services_fn`` to ``create_app(...)``.
- Contributes a health ping that appears in ``/api/v1/health/deep``.

Structure:
- Protocol (``AuthSvcP``)
- Concrete implementation (``AuthSvc``)
- Factory (``make_auth_svc``) — resolves Settings from svcs container
- Ping (``ping_auth_svc``) — simple invocation to verify wiring
"""

from __future__ import annotations

import contextlib
import secrets
import time
from typing import TYPE_CHECKING

import jwt
import pydantic
import structlog

from kumacub import config

# noinspection PyCompatibility
from . import exceptions, models, protocols

if TYPE_CHECKING:
    import svcs


class AuthSvc:
    """Authentication service implementation."""

    def __init__(self, service_name: str, auth_settings: config.AuthSettings, jwt_settings: config.JWTSettings) -> None:
        """Initialize the AuthSvc with settings.

        Args:
            service_name: The name of the service (for JWT claims).
            auth_settings: Application settings containing auth configuration.
            jwt_settings: Application settings containing JWT configuration.
        """
        self._service_name: str = service_name
        self._auth_settings: config.AuthSettings = auth_settings
        self._jwt_settings: config.JWTSettings = jwt_settings

    def create_token(self, sub: str) -> models.Token:
        """Create a JWT for the given username.

        Args:
            sub: The subject (username) to include in the token.

        Returns:
            Token object containing access_token, token_type, and expires_in.

        Raises:
            KumaCubAuthSigningSecretNotConfiguredError: If JWT secret is not configured.
        """
        if not self._jwt_settings.secret:
            raise exceptions.KumaCubAuthSigningSecretNotConfiguredError

        claims = {
            "iss": self._service_name,
            "aud": self._service_name,
            "exp": int(time.time()) + int(self._jwt_settings.expire_seconds),
            "sub": sub,
        }
        token = jwt.encode(claims, self._jwt_settings.secret, algorithm=self._jwt_settings.algorithm)
        return models.Token(
            access_token=str(token),
            expires_in=self._jwt_settings.expire_seconds,
            token_type="Bearer",  # noqa: S106 - Constant token type string is not a secret
        )

    def extract_claims(self, token: str | None) -> models.Claims:
        """Extract and validate claims from a provided token string.

        Args:
            token: The JWT to extract claims from.

        Returns: A set of claims. If auth is disabled, claims will include sub=anonymous.

        Raises:
            KumaCubAuthInvalidTokenError: If token is missing/empty or verification fails.
            KumaCubAuthIssuerNotAllowedError: If the token issuer does not match the configured service name.
            KumaCubAuthSigningSecretNotConfiguredError: If the signing secret is not configured.
        """
        if not self._auth_settings.required:
            return models.Claims(iss=self._service_name, aud=self._service_name, exp=0, sub="anonymous")

        if not token:
            msg = "Missing or empty authorization token"
            raise exceptions.KumaCubAuthInvalidTokenError(msg)

        try:
            claims = self.verify_token(token)
        except exceptions.KumaCubAuthError as e:
            structlog.get_logger().warning("auth_failed", reason=str(e))
            raise

        if claims.sub:  # Bind identity into structured logs.
            structlog.contextvars.bind_contextvars(username=claims.sub)
        return claims

    def refresh_token(self, token: str) -> models.Token:
        """Refresh a JWT with a new expiration.

        Args:
            token: The existing JWT to refresh.

        Returns:
            New token with refreshed expiration.

        Raises:
            KumaCubAuthInvalidTokenError: If token is invalid.
            KumaCubAuthIssuerNotAllowedError: If the token issuer does not match the configured service name.
            KumaCubAuthSigningSecretNotConfiguredError: If the signing secret is not configured.
        """
        claims = self.verify_token(token)
        return self.create_token(claims.sub)

    def validate_credentials(self, username: str, password: str) -> None:
        """Validate username/password credentials.

        Args:
            username: The username to validate.
            password: The password to validate.

        Raises:
            KumaCubAuthNotConfiguredError: If auth is not configured.
            KumaCubAuthInvalidCredentials: If provided credentials are invalid.
        """
        if not self._auth_settings.username or not self._auth_settings.password:
            raise exceptions.KumaCubAuthNotConfiguredError

        pwd_field = self._auth_settings.password
        configured_password = pwd_field.get_secret_value() if isinstance(pwd_field, pydantic.SecretStr) else ""

        # Constant-time compare to mitigate timing attacks for both fields
        user_ok = secrets.compare_digest(username or "", self._auth_settings.username)
        pass_ok = secrets.compare_digest(password or "", configured_password)
        if not (user_ok and pass_ok):
            raise exceptions.KumaCubAuthInvalidCredentialsError

    def verify_token(self, token: str) -> models.Claims:
        """Verify a JWT and return validated claims.

        Args:
            token: The JWT to verify.

        Returns:
            Validated Claims object.

        Raises:
            KumaCubAuthInvalidTokenError: If token is invalid or verification fails.
            KumaCubAuthIssuerNotAllowedError: If the token issuer does not match the configured service name.
            KumaCubAuthSigningSecretNotConfiguredError: If the signing secret is not configured.
        """
        if not self._jwt_settings.secret:
            raise exceptions.KumaCubAuthSigningSecretNotConfiguredError

        try:
            claims_map = jwt.decode(
                token,
                key=self._jwt_settings.secret,
                algorithms=[self._jwt_settings.algorithm],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "require": ["aud", "exp", "iss", "sub"],
                },
                audience=self._service_name,
                issuer=self._service_name,
                leeway=self._jwt_settings.leeway_seconds,
            )
        except jwt.InvalidIssuerError as e:
            raise exceptions.KumaCubAuthIssuerNotAllowedError from e
        except jwt.InvalidTokenError as e:
            raise exceptions.KumaCubAuthInvalidTokenError from e

        try:
            return models.Claims.model_validate(claims_map)
        except pydantic.ValidationError as e:
            msg = "Invalid token: claims failed validation"
            raise exceptions.KumaCubAuthInvalidTokenError(msg) from e


def make_auth_svc(container: svcs.Container) -> protocols.AuthSvcP:
    """Create an AuthSvc instance.

    Args:
        container: The service container that provides access to configuration.

    Returns:
        A configured AuthSvc instance.
    """
    settings = container.get_abstract(config.Settings)
    return AuthSvc(service_name=settings.service_name, auth_settings=settings.auth, jwt_settings=settings.jwt)


async def ping_auth_svc(client: protocols.AuthSvcP) -> None:
    """Ping auth service.

    Registered as a health ping so it is executed by ``/api/v1/health/deep``.
    """
    # Simple validation that the service is properly configured.
    # This doesn't actually validate credentials, just checks basic functionality.
    with contextlib.suppress(exceptions.KumaCubAuthError):
        # Test credential validation with dummy data (should raise on invalid)
        client.validate_credentials("dummy", "dummy")
