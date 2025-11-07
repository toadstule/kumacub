#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Uptime Kuma service."""


class KumaSvc:
    """Uptime Kuma Service.

    def __init__(self, url: str) -> None:
        ""Initialize a KumaSvc instance.""
        self._base_url = url
        self._client: httpx.AsyncClient | httpx.Client | None = None

    async def __aenter__(self) -> "KumaSvc":
        ""Enter async context manager.""
        self._client = httpx.AsyncClient(base_url=self._base_url)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        ""Exit async context manager.""
        if self._client:
            await self._client.aclose()

    def __enter__(self) -> "KumaSvc":
        ""Enter context manager.""
        self._client = httpx.Client(base_url=self._base_url)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        ""Exit context manager.""
        if self._client:
            self._client.close()
    """
