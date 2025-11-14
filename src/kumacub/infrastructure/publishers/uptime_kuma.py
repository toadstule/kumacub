#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Uptime Kuma publisher."""

from typing import ClassVar, Literal

import httpx
import pydantic
import structlog


class UptimeKumaPublishArgs(pydantic.BaseModel):
    """Arguments for the publisher."""

    id: str
    url: str
    push_token: pydantic.SecretStr
    status: Literal["", "down", "up"] = ""
    msg: str = pydantic.Field(default="", max_length=250)
    ping: pydantic.PositiveFloat | None


class _UptimeKumaPublisher:
    """Uptime Kuma publisher implementing the publisher protocol."""

    name: ClassVar[str] = "uptime_kuma"

    def __init__(self) -> None:
        """Initialize an UptimeKumaPublisher instance."""
        self._logger = structlog.get_logger()

    async def publish(self, args: UptimeKumaPublishArgs) -> None:
        """Publish a check result to Uptime Kuma."""
        # Cast to specific args type for this publisher
        url = f"{args.url}/api/push/{args.push_token.get_secret_value()}"
        params = {
            k: v
            for k, v in args.model_dump(mode="json", exclude_none=True, exclude_unset=True).items()
            if k in {"status", "msg", "ping"}
        }
        self._logger.debug("Pushing check result to Uptime Kuma", id=args.id, url=url, params=params)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url=url,
                    params=params,
                    headers={"Accept": "application/json"},
                    follow_redirects=True,
                    timeout=10.0,
                )
                response.raise_for_status()
                self._logger.debug("Successfully pushed check result to Uptime Kuma", id=args.id)

        except httpx.HTTPStatusError as e:
            error_msg = e.response.json().get("msg", f"Server returned error: {e.response.status_code}")
            self._logger.warning("Failed to push check result: %s", error_msg, id=args.id)

        except httpx.RequestError as e:
            error_msg = f"Request failed: {e!s}"
            self._logger.warning("Failed to push check result: %s", error_msg, id=args.id)
