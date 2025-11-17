#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Stdout publisher."""

from typing import ClassVar, Literal

import pydantic


class StdoutPublishArgs(pydantic.BaseModel):
    """Arguments for the publisher."""

    id: str
    status: Literal["", "down", "up"] = ""
    msg: str = pydantic.Field(default="", max_length=250)


class _StdoutPublisher:
    """Stdout publisher implementing the publisher protocol."""

    name: ClassVar[str] = "stdout"

    @staticmethod
    async def publish(args: StdoutPublishArgs) -> None:
        """Publish a check result to stdout."""
        print(args.model_dump_json(indent=2))
