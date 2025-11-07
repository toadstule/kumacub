#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Auth service."""

from .exceptions import (  # noqa: I001
    KumaCubAuthNotConfiguredError,
    KumaCubAuthInvalidCredentialsError,
    KumaCubAuthInvalidTokenError,
    KumaCubAuthIssuerNotAllowedError,
    KumaCubAuthError,
    KumaCubAuthSigningSecretNotConfiguredError,
)
from .service import AuthSvc, make_auth_svc, ping_auth_svc
from .models import Claims, Token
from .protocols import AuthSvcP

__all__ = [
    "AuthSvc",
    "AuthSvcP",
    "Claims",
    "KumaCubAuthError",
    "KumaCubAuthInvalidCredentialsError",
    "KumaCubAuthInvalidTokenError",
    "KumaCubAuthIssuerNotAllowedError",
    "KumaCubAuthNotConfiguredError",
    "KumaCubAuthSigningSecretNotConfiguredError",
    "Token",
    "make_auth_svc",
    "ping_auth_svc",
]
