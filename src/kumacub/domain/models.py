#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.


"""KumaCub data models."""

from typing import Literal

import pydantic


class Executor(pydantic.BaseModel):
    """KumaCub Executor."""

    name: Literal["process"] = "process"
    command: str
    args: list[str] = []
    env: dict[str, str] = {}


class Parser(pydantic.BaseModel):
    """KumaCub Parser."""

    name: Literal["nagios"] = "nagios"


class Publisher(pydantic.BaseModel):
    """KumaCub Publisher."""

    name: Literal["uptime_kuma"] = "uptime_kuma"
    url: str
    push_token: pydantic.SecretStr


class Schedule(pydantic.BaseModel):
    """KumaCub Schedule."""

    interval: pydantic.PositiveFloat = 60


class Check(pydantic.BaseModel):
    """KumaCub Check."""

    name: str
    executor: Executor
    parser: Parser = Parser()
    publisher: Publisher
    schedule: Schedule = Schedule()
