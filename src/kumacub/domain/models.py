#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.


"""KumaCub data models."""

from typing import Annotated, Any, Literal, TypeAlias

import pydantic
from pydantic import Field, model_validator


class Executor(pydantic.BaseModel):
    """KumaCub Executor."""

    name: Literal["process"] = "process"
    command: str
    args: list[str] = []
    env: dict[str, str] = {}


class Parser(pydantic.BaseModel):
    """KumaCub Parser."""

    name: Literal["nagios"] = "nagios"


class StdoutPublisher(pydantic.BaseModel):
    """Stdout Publisher."""

    name: Literal["stdout"] = "stdout"
    url: str = ""
    push_token: pydantic.SecretStr = pydantic.SecretStr("")


class UptimeKumaPublisher(pydantic.BaseModel):
    """Uptime Kuma Publisher."""

    name: Literal["uptime_kuma"] = "uptime_kuma"
    url: str
    push_token: pydantic.SecretStr


# Discriminated union allows Pydantic to select the correct publisher class
# based on the 'name' field and validate required fields accordingly
AnyPublisher: TypeAlias = Annotated[
    StdoutPublisher | UptimeKumaPublisher,
    Field(discriminator="name"),
]


class Schedule(pydantic.BaseModel):
    """KumaCub Schedule."""

    interval: pydantic.PositiveFloat = 60


class Check(pydantic.BaseModel):
    """KumaCub Check."""

    name: str
    executor: Executor
    parser: Parser = Parser()
    publisher: AnyPublisher
    schedule: Schedule = Schedule()

    @model_validator(mode="before")
    @classmethod
    def set_default_publisher_name(cls, data: Any) -> Any:  # noqa: ANN401
        """Set default publisher name to 'uptime_kuma' if not specified."""
        if isinstance(data, dict):
            publisher = data.get("publisher")
            if isinstance(publisher, dict) and "name" not in publisher:
                publisher["name"] = "uptime_kuma"
        return data
