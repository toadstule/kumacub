#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Uptime Kuma service."""

import httpx
import structlog

from kumacub.services.kuma_svc import models


class KumaSvc:
    """Uptime Kuma Service."""

    def __init__(self, url: str) -> None:
        """Initialize a KumaSvc instance."""
        self._base_url = url.rstrip("/")
        self._logger = structlog.get_logger()

    async def ping(self) -> bool:
        """Ping the Uptime Kuma server.

        Returns:
            bool: True if the ping was successful, False otherwise.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url=f"{self._base_url}/api/entry-page",
                    headers={"Accept": "application/json"},
                    follow_redirects=True,
                    timeout=10.0,
                )
                response.raise_for_status()
                self._logger.debug("Successfully pinged Uptime Kuma server")
                return True
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            self._logger.warning("Failed to ping Uptime Kuma server", error=str(e))
            return False

    async def push(self, push_token: str, parameters: models.PushParameters) -> models.PushResponse:
        """Push a check result to Uptime Kuma.

        Args:
            push_token: The Push token.
            parameters: The check result parameters to push.

        Returns:
            PushResponse: The response from the server with success status and optional message.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url=f"{self._base_url}/api/push/{push_token}",
                    params=parameters.model_dump(mode="json", exclude_none=True, exclude_unset=True),
                    headers={"Accept": "application/json"},
                    follow_redirects=True,
                    timeout=10.0,
                )
                response.raise_for_status()
                self._logger.debug("Successfully pushed check result to Uptime Kuma")
                return models.PushResponse(ok=True, msg=None)

        except httpx.HTTPStatusError as e:
            error_msg = e.response.json().get("msg", f"Server returned error: {e.response.status_code}")
            self._logger.warning("Failed to push check result: %s", error_msg)
            return models.PushResponse(ok=False, msg=error_msg)

        except httpx.RequestError as e:
            error_msg = f"Request failed: {e!s}"
            self._logger.warning("Failed to push check result: %s", error_msg)
            return models.PushResponse(ok=False, msg=error_msg)
