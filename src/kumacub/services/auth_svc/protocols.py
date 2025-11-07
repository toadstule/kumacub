#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Authentication service schemas -- interfaces, models and types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from . import models


@runtime_checkable
class AuthSvcP(Protocol):
    """Interface for authentication service."""

    def create_token(self, sub: str) -> models.Token:
        """Create a JWT for the given subject."""
        ...

    def extract_claims(self, token: str | None) -> models.Claims:
        """Extract and validate claims from a provided token string (or None)."""
        ...

    def refresh_token(self, token: str) -> models.Token:
        """Refresh a JWT with a new expiration."""
        ...

    def validate_credentials(self, username: str, password: str) -> None:
        """Validate username/password credentials."""
        ...

    def verify_token(self, token: str) -> models.Claims:
        """Verify a JWT and return validated claims."""
        ...
