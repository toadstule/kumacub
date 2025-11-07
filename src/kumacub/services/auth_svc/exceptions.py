#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Authentication exceptions."""

from kumacub.exceptions import KumaCubError


class KumaCubAuthError(KumaCubError):
    """Authentication error."""


class KumaCubAuthInvalidCredentialsError(KumaCubAuthError):
    """Provided username/password credentials are invalid."""


class KumaCubAuthInvalidTokenError(KumaCubAuthError):
    """Token is invalid."""


class KumaCubAuthIssuerNotAllowedError(KumaCubAuthError):
    """Token issuer is not allowed."""


class KumaCubAuthNotConfiguredError(KumaCubAuthError):
    """Auth credentials or configuration missing/disabled."""


class KumaCubAuthSigningSecretNotConfiguredError(KumaCubAuthError):
    """JWT signing secret not configured."""
