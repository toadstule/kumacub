"""Authentication service schemas -- interfaces, models and types."""


#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

from typing import Annotated, Literal

import pydantic


class Claims(pydantic.BaseModel):
    """Strict claims schema used after signature/claim verification."""

    aud: Annotated[str, pydantic.StringConstraints(strip_whitespace=True, min_length=1)]
    exp: int
    iss: Annotated[str, pydantic.StringConstraints(strip_whitespace=True, min_length=1)]
    sub: Annotated[str, pydantic.StringConstraints(strip_whitespace=True, min_length=1)]


class Token(pydantic.BaseModel):
    """Token model returned by token creation and refresh."""

    access_token: Annotated[str, pydantic.StringConstraints(strip_whitespace=True, min_length=1)]
    token_type: Literal["Bearer"]
    expires_in: int
