#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.


"""KumaCub types."""

from typing import Literal

import pydantic


class Check(pydantic.BaseModel):
    """KumaCub Check."""

    name: str
    type: Literal["nagios"]
    command: str
    args: list[str] = []
    env: dict[str, str] = {}
    interval: pydantic.PositiveFloat = 60


class CheckResult(pydantic.BaseModel):
    """KumaCub Check Result."""

    status: Literal["", "down", "up"] = "up"
    msg: str = pydantic.Field(default="", max_length=250)
    ping: pydantic.PositiveFloat | None = None
