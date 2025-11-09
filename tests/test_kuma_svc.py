#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Tests for the KumaSvc class."""

from typing import Any, Literal

import httpx
import pytest
import respx

from kumacub.services.kuma_svc import KumaSvc
from kumacub.services.kuma_svc.models import PushParameters


class TestKumaSvc:
    """Tests for KumaSvc class."""

    @pytest.fixture
    def base_url(self) -> str:
        """Return the base URL for testing."""
        return "http://test-server:3001"

    @pytest.fixture
    def kuma_svc(self, base_url: str) -> KumaSvc:
        """Return a KumaSvc instance for testing."""
        return KumaSvc(url=base_url)

    @pytest.fixture
    def push_parameters(self) -> PushParameters:
        """Return sample push parameters for testing."""
        return PushParameters(status="up", msg="Test message", ping=42.5)

    @pytest.mark.asyncio
    async def test_ping_success(self, kuma_svc: KumaSvc) -> None:
        """Test successful ping."""
        with respx.mock() as mock:
            mock.get(f"{kuma_svc._base_url}/api/entry-page").respond(httpx.codes.OK, json={})
            assert await kuma_svc.ping() is True

    @pytest.mark.asyncio
    async def test_ping_failure(self, kuma_svc: KumaSvc) -> None:
        """Test failed ping."""
        with respx.mock() as mock:
            mock.get(f"{kuma_svc._base_url}/api/entry-page").respond(httpx.codes.INTERNAL_SERVER_ERROR)
            assert await kuma_svc.ping() is False

    @pytest.mark.asyncio
    async def test_push_success(self, kuma_svc: KumaSvc, push_parameters: PushParameters) -> None:
        """Test successful push."""
        with respx.mock() as mock:
            mock.get(f"{kuma_svc._base_url}/api/push/test-token").respond(httpx.codes.OK, json={"ok": True})

            result = await kuma_svc.push("test-token", push_parameters)

            assert result.ok is True
            assert result.msg is None

            # Verify the request was made with the correct parameters
            request = mock.calls[0][0]
            assert request.method == "GET"
            assert request.url.path == "/api/push/test-token"
            assert request.url.params["status"] == "up"
            assert request.url.params["msg"] == "Test message"
            assert request.url.params["ping"] == "42.5"
            assert request.headers["accept"] == "application/json"

    @pytest.mark.asyncio
    async def test_push_http_error_with_message(self, kuma_svc: KumaSvc, push_parameters: PushParameters) -> None:
        """Test push with HTTP error that includes a message."""
        with respx.mock() as mock:
            mock.get(f"{kuma_svc._base_url}/api/push/test-token").respond(
                httpx.codes.NOT_FOUND, json={"ok": False, "msg": "Monitor not found or not active"}
            )

            result = await kuma_svc.push("test-token", push_parameters)

            assert result.msg == "Monitor not found or not active"

    @pytest.mark.asyncio
    async def test_push_http_error_no_message(self, kuma_svc: KumaSvc, push_parameters: PushParameters) -> None:
        """Test push with HTTP error that doesn't include a message."""
        with respx.mock() as mock:
            mock.get(f"{kuma_svc._base_url}/api/push/test-token").respond(
                httpx.codes.INTERNAL_SERVER_ERROR, json={"ok": False, "msg": "Internal server error"}
            )

            result = await kuma_svc.push("test-token", push_parameters)

            assert result.ok is False
            assert result.msg == "Internal server error"

    @pytest.mark.asyncio
    async def test_push_request_error(self, kuma_svc: KumaSvc, push_parameters: PushParameters) -> None:
        """Test push with request error."""
        with respx.mock() as mock:
            mock.get(f"{kuma_svc._base_url}/api/push/test-token").mock(
                side_effect=httpx.RequestError("Connection error")
            )
            result = await kuma_svc.push("test-token", push_parameters)
            assert result.msg is not None
            assert "Request failed: Connection error" in result.msg

    @pytest.mark.parametrize(
        ("status", "msg", "ping", "expected_params"),
        [
            ("up", "Test", 1.0, {"status": "up", "msg": "Test", "ping": "1.0"}),
            ("down", "", None, {"status": "down", "msg": ""}),
        ],
    )
    @pytest.mark.asyncio
    async def test_push_parameters_serialization(
        self,
        kuma_svc: KumaSvc,
        status: Literal["up", "down"],
        msg: str,
        ping: float | None,
        expected_params: dict[str, Any],
    ) -> None:
        """Test that push parameters are correctly serialized to query params."""
        with respx.mock() as mock:
            # Mock the response
            mock.get(f"{kuma_svc._base_url}/api/push/test-token").respond(httpx.codes.OK, json={"ok": True})

            # Create parameters and make the request
            params = PushParameters(status=status, msg=msg, ping=ping)
            await kuma_svc.push("test-token", params)

            # Get the request that was made
            request = mock.calls[0][0]

            # Check the URL and method
            assert request.method == "GET"
            assert request.url.path == "/api/push/test-token"

            # Check that all expected parameters are present in the URL query string
            for key, expected_value in expected_params.items():
                if expected_value is not None:
                    assert request.url.params[key] == expected_value
