#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Auth API tests using a DI-registered FakeAuthSvc.

This mirrors uses a raise_on pattern to exercise api/v1/auth.py branches
without relying on real JWT internals. It validates header parsing, error
mapping, and success paths for the auth endpoints.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from starlette import status

from kumacub import config
from kumacub.app import create_app
from kumacub.services import auth_svc

if TYPE_CHECKING:
    from collections.abc import Generator

    import svcs


class FakeAuthSvc(auth_svc.AuthSvcP):
    """In-memory fake for AuthSvc with a simple raise_on mechanism.

    raise_on: a set of method names to trigger specific exceptions.
    - "not_configured": validate_credentials -> KumaCubAuthNotConfiguredError
    - "missing_secret": create_token -> KumaCubAuthSigningSecretNotConfiguredError
    - "invalid_creds": validate_credentials -> returns False (no exception)
    - "issuer_not_allowed": refresh_token/verify_token -> KumaCubAuthIssuerNotAllowedError
    - "invalid_token": refresh_token/verify_token/extract_claims -> KumaCubAuthInvalidTokenError
    """

    def __init__(self, *, raise_on: set[str] | None = None) -> None:
        """Initialize fake with optional set of behaviors to raise on."""
        self._raise_on = raise_on or set()
        self._settings = config.get_settings()

    # ---- AuthSvcP interface ----
    def create_token(self, username: str) -> auth_svc.Token:
        """Return a token for the username or raise secret-not-configured."""
        if "missing_secret" in self._raise_on:
            raise auth_svc.KumaCubAuthSigningSecretNotConfiguredError
        # Return a minimal plausible token payload
        return auth_svc.Token(access_token=f"token-for:{username}", token_type="Bearer", expires_in=60)  # noqa: S106

    def extract_claims(self, token: str | None) -> auth_svc.Claims:
        """Return claims or raise KumaCubAuthInvalidTokenError for bad/missing tokens."""
        if not self._settings.auth.required:
            return auth_svc.Claims(iss="my-api", aud="my-api", exp=0, sub="anonymous")
        # Treat None, empty, or whitespace-only tokens as missing
        if token is None or (isinstance(token, str) and not token.strip()):
            raise auth_svc.KumaCubAuthInvalidTokenError
        if "invalid_token" in self._raise_on:
            raise auth_svc.KumaCubAuthInvalidTokenError
        # Return valid claims for authenticated user
        return auth_svc.Claims(iss="my-api", aud="my-api", exp=9999999999, sub="user")

    def refresh_token(self, token: str) -> auth_svc.Token:
        """Return a refreshed token or raise based on configured conditions."""
        if not token:
            raise auth_svc.KumaCubAuthInvalidTokenError
        if "issuer_not_allowed" in self._raise_on:
            raise auth_svc.KumaCubAuthIssuerNotAllowedError
        if "invalid_token" in self._raise_on:
            raise auth_svc.KumaCubAuthInvalidTokenError
        if "missing_secret" in self._raise_on:
            raise auth_svc.KumaCubAuthSigningSecretNotConfiguredError
        return auth_svc.Token(access_token=f"refreshed:{token}", token_type="Bearer", expires_in=60)  # noqa: S106

    def validate_credentials(self, username: str, password: str) -> None:
        """Validate username/password or simulate not-configured/invalid cases."""
        del username, password  # unused
        if "not_configured" in self._raise_on:
            raise auth_svc.KumaCubAuthNotConfiguredError
        if "invalid_creds" in self._raise_on:
            raise auth_svc.KumaCubAuthInvalidCredentialsError

    def verify_token(self, _token: str) -> auth_svc.Claims:
        """Return valid claims or raise based on configured conditions."""
        if "issuer_not_allowed" in self._raise_on:
            raise auth_svc.KumaCubAuthIssuerNotAllowedError
        if "invalid_token" in self._raise_on:
            raise auth_svc.KumaCubAuthInvalidTokenError
        return auth_svc.Claims(iss="my-api", aud="my-api", exp=9999999999, sub="user")


@pytest.fixture
def client(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    """Build a TestClient with a DI-registered FakeAuthSvc.

    Parameterize by passing a dict via pytest.mark.parametrize(..., indirect=True):
      {"raise_on": {"invalid_token", ...}}
    """
    params = getattr(request, "param", {})
    raise_on = params.get("raise_on", set())
    auth_required = params.get("auth_required", False)
    use_fake = params.get("use_fake", True)
    extra_env: dict[str, str] = params.get("env", {})

    def registrar(registry: svcs.Registry) -> None:
        if use_fake:
            fake = FakeAuthSvc(raise_on=raise_on)
            registry.register_value(auth_svc.AuthSvcP, fake)
        else:
            # Register the real auth service factory so endpoints can resolve it
            registry.register_factory(auth_svc.AuthSvcP, auth_svc.make_auth_svc, ping=auth_svc.ping_auth_svc)

    # Configure env for the app instance created in this test
    monkeypatch.setenv("AUTH__REQUIRED", str(auth_required).upper())
    for k, v in extra_env.items():
        monkeypatch.setenv(k, v)
    # Ensure we don't leak env into other tests
    try:
        config.reload_settings()
        with TestClient(create_app(register_services_fn=registrar), raise_server_exceptions=False) as c:
            yield c
    finally:
        os.environ.pop("AUTH__REQUIRED", None)


def _oauth2pw(user: str, pwd: str) -> dict[str, str]:
    return {"grant_type": "password", "username": user, "password": pwd}


def _bearer(tok: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {tok}"}


def test_login_success(client: TestClient) -> None:
    """Login succeeds with valid credentials using the fake service."""
    res = client.post("/api/v1/auth", data=_oauth2pw("user", "pass"))
    assert res.status_code == status.HTTP_200_OK
    body = res.json()
    assert body["access_token"].startswith("token-for:")
    assert body["token_type"] == "Bearer"  # noqa: S105


def test_login_missing_basic_header_401(client: TestClient) -> None:
    """Login without Basic Authorization header should return 422."""
    res = client.post("/api/v1/auth")
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize("client", [{"raise_on": {"invalid_creds"}}], indirect=True)
def test_login_invalid_credentials_401(client: TestClient) -> None:
    """Login fails with 401 when fake returns invalid credentials."""
    res = client.post("/api/v1/auth", data=_oauth2pw("user", "wrong"))
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("client", [{"raise_on": {"not_configured"}}], indirect=True)
def test_login_not_configured_503(client: TestClient) -> None:
    """Login returns 503 when KumaCubAuthNotConfiguredError is raised by the service."""
    res = client.post("/api/v1/auth", data=_oauth2pw("user", "pass"))
    assert res.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


@pytest.mark.parametrize("client", [{"raise_on": {"missing_secret"}}], indirect=True)
def test_login_missing_secret_500(client: TestClient) -> None:
    """Login returns 500 when secret is not configured (service raises)."""
    res = client.post("/api/v1/auth", data=_oauth2pw("user", "pass"))
    assert res.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert res.json()["detail"] == "JWT signing secret not configured."


def test_refresh_missing_token_401(client: TestClient) -> None:
    """Refresh without Authorization header returns 401 Missing token."""
    res = client.post("/api/v1/auth/refresh")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json()["detail"] == "Token is invalid."


@pytest.mark.parametrize("client", [{"raise_on": {"issuer_not_allowed"}}], indirect=True)
def test_refresh_issuer_mismatch_403(client: TestClient) -> None:
    """Refresh returns 403 when fake raises KumaCubAuthIssuerNotAllowedError."""
    res = client.post("/api/v1/auth/refresh", headers=_bearer("any"))
    assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    "client",
    [
        {
            "auth_required": True,
            "use_fake": False,
            "env": {"AUTH__USERNAME": "user", "AUTH__PASSWORD": "pass", "JWT__SECRET": "devsecret"},
        }
    ],
    indirect=True,
)
def test_verify_missing_token_401(client: TestClient) -> None:
    """Verify requires a Bearer token in Authorization header when auth is enabled."""
    res = client.post("/api/v1/auth/verify")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json()["detail"] == "Token is invalid."


def test_verify_valid_with_bearer_token(client: TestClient) -> None:
    """Verify succeeds when a valid Bearer token is provided in Authorization header."""
    # First login to get a token
    res = client.post("/api/v1/auth", data=_oauth2pw("user", "pass"))
    token = res.json()["access_token"]

    res2 = client.post("/api/v1/auth/verify", headers=_bearer(token))
    assert res2.status_code == status.HTTP_200_OK
    assert res2.json() == {"valid": True}


@pytest.mark.parametrize(
    "client",
    [
        {
            "auth_required": True,
            "use_fake": False,
            "env": {"AUTH__USERNAME": "user", "AUTH__PASSWORD": "pass", "JWT__SECRET": "devsecret"},
        }
    ],
    indirect=True,
)
def test_verify_empty_bearer_token_401(client: TestClient) -> None:
    """Empty Bearer token in Authorization header returns 401 when auth is enabled."""
    # Provide an empty Bearer token in header
    res = client.post(
        "/api/v1/auth/verify",
        headers={"Authorization": "Bearer   "},
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json()["detail"] == "Token is invalid."


@pytest.mark.parametrize("client", [{"raise_on": {"invalid_token"}}], indirect=True)
def test_verify_invalid_bearer_token_401(client: TestClient) -> None:
    """Invalid Bearer token in Authorization header returns 401."""
    res = client.post(
        "/api/v1/auth/verify",
        headers={"Authorization": "Bearer bad"},
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json()["detail"] == "Token is invalid."


@pytest.mark.parametrize(
    "client",
    [
        {
            "auth_required": True,
            "use_fake": False,
            "env": {"AUTH__USERNAME": "user", "AUTH__PASSWORD": "pass", "JWT__SECRET": "devsecret"},
        }
    ],
    indirect=True,
)
def test_verify_unsupported_token_scheme_401(client: TestClient) -> None:
    """Unsupported token schemes (like legacy Token) should return 401 when auth is enabled."""
    res = client.post("/api/v1/auth/verify", headers={"Authorization": "Token something"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json()["detail"] == "Token is invalid."


@pytest.mark.parametrize("client", [{"raise_on": {"invalid_token"}}], indirect=True)
def test_refresh_invalid_token_maps_401_with_message(client: TestClient) -> None:
    """refresh() maps KumaCubAuthInvalidTokenError to 401 with detail from exception."""
    res = client.post("/api/v1/auth/refresh", headers=_bearer("any"))
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json()["detail"] == "Token is invalid."


@pytest.mark.parametrize("client", [{"raise_on": {"missing_secret"}}], indirect=True)
def test_refresh_missing_secret_500(client: TestClient) -> None:
    """refresh() maps KumaCubAuthSigningSecretNotConfiguredError to 500."""
    # Directly call refresh; fake will raise KumaCubAuthSigningSecretNotConfiguredError
    res2 = client.post("/api/v1/auth/refresh", headers=_bearer("any"))
    assert res2.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert res2.json()["detail"] == "JWT signing secret not configured."


@pytest.mark.parametrize("client", [{"raise_on": {"invalid_token"}}], indirect=True)
def test_verify_invalid_token_maps_401(client: TestClient) -> None:
    """verify() maps KumaCubAuthInvalidTokenError to 401 with detail from exception."""
    res = client.post("/api/v1/auth/verify", headers=_bearer("any"))
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json()["detail"] == "Token is invalid."


def test_verify_bearer_header_success(client: TestClient) -> None:
    """verify() accepts Bearer header and returns {valid: True}."""
    # Any token value works with the fake auth service
    res = client.post("/api/v1/auth/verify", headers=_bearer("something"))
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == {"valid": True}


@pytest.mark.parametrize("client", [{"auth_required": True}], indirect=True)
def test_me_unauthorized_when_required_without_token(client: TestClient) -> None:
    """/me returns 401 when auth.required is true and no token is provided."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("client", [{"auth_required": False}], indirect=True)
def test_me_returns_anonymous_when_auth_disabled(client: TestClient) -> None:
    """/me returns anonymous identity when auth.required is false (default)."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["username"] == "anonymous"


@pytest.mark.parametrize(
    "client",
    [
        {
            "auth_required": True,
            "use_fake": False,
            "env": {"AUTH__USERNAME": "user", "AUTH__PASSWORD": "pass", "JWT__SECRET": "devsecret"},
        }
    ],
    indirect=True,
)
def test_me_returns_identity_when_required_and_token_provided(client: TestClient) -> None:
    """/me returns user identity when auth.required is true and token is present."""
    # Get a token via login
    res = client.post("/api/v1/auth", data=_oauth2pw("user", "pass"))
    assert res.status_code == status.HTTP_200_OK
    token = res.json()["access_token"]
    res_me = client.get("/api/v1/auth/me", headers=_bearer(token))
    assert res_me.status_code == status.HTTP_200_OK
    assert res_me.json()["username"] == "user"
