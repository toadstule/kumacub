#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.


"""KumaCub data models."""

from typing import Annotated, Literal, TypeAlias

import pydantic
from pydantic import Field


class Executor(pydantic.BaseModel):
    """KumaCub Executor."""

    name: Literal["process"] = "process"
    command: str
    args: list[str] = []
    env: dict[str, str] = {}


class Parser(pydantic.BaseModel):
    """KumaCub Parser."""

    name: Literal["nagios"] = "nagios"


# Publisher type definitions and utilities
PublisherName: TypeAlias = Literal["stdout", "uptime_kuma"]


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


# Mapping of publisher names to their respective model classes
PUBLISHER_TYPES: dict[PublisherName, type[StdoutPublisher] | type[UptimeKumaPublisher]] = {
    "stdout": StdoutPublisher,
    "uptime_kuma": UptimeKumaPublisher,
}

# The union type with discriminator
AnyPublisher: TypeAlias = Annotated[
    StdoutPublisher | UptimeKumaPublisher,
    Field(discriminator="name"),
]


def create_publisher(
    name: PublisherName,
    url: str | None = None,
    push_token: str | pydantic.SecretStr | None = None,
) -> StdoutPublisher | UptimeKumaPublisher:
    """Create a publisher instance based on the provided arguments.

    Args:
        name: The type of publisher to create ("stdout" or "uptime_kuma").
        url: The URL for the Uptime Kuma instance (required for uptime_kuma).
        push_token: The push token for authentication (required for uptime_kuma).

    Returns:
        An instance of the appropriate publisher type.

    Raises:
        ValueError: If required fields are missing for the specified publisher type.
    """
    if name == "stdout":
        return StdoutPublisher()

    if name == "uptime_kuma":
        if url is None or push_token is None:
            msg = "url and push_token are required for UptimeKumaPublisher"
            raise ValueError(msg)
        # Convert push_token to SecretStr if it's a string
        secret_token = pydantic.SecretStr(push_token) if isinstance(push_token, str) else push_token
        return UptimeKumaPublisher(url=url, push_token=secret_token)

    msg = f"Unknown publisher name: {name}"
    raise ValueError(msg)


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

    # No backward compatibility layer - publisher.name is now required
