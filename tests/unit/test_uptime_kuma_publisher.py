#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Tests for the UptimeKumaPublisher class."""

from typing import Any, Literal

import httpx
import pytest
import respx

from kumacub.infrastructure.publishers import uptime_kuma


class TestUptimeKumaPublisher:
    """Tests for UptimeKumaPublisher class."""

    @pytest.fixture
    def uptime_kuma_publisher(self) -> uptime_kuma.UptimeKumaPublisher:
        """Return a UptimeKumaPublisher instance for testing."""
        return uptime_kuma.UptimeKumaPublisher()

    @pytest.fixture
    def publish_args(self) -> uptime_kuma.UptimeKumaPublishArgs:
        """Return sample publish args for testing."""
        return uptime_kuma.UptimeKumaPublishArgs(
            url="http://ignored",
            push_token="test-token",  # noqa: S106
            status="up",
            msg="Test message",
            ping=42.5,
        )

    @pytest.mark.asyncio
    async def test_publish_success(
        self, uptime_kuma_publisher: uptime_kuma.UptimeKumaPublisher, publish_args: uptime_kuma.UptimeKumaPublishArgs
    ) -> None:
        """Test successful publish."""
        with respx.mock() as mock:
            mock.get(f"{publish_args.url}/api/push/test-token").respond(httpx.codes.OK, json={"ok": True})
            await uptime_kuma_publisher.publish(publish_args)

            # Verify the request was made with the correct parameters
            request = mock.calls[0][0]
            assert request.method == "GET"
            assert request.url.path == "/api/push/test-token"
            assert request.url.params["status"] == "up"
            assert request.url.params["msg"] == "Test message"
            assert request.url.params["ping"] == "42.5"
            assert request.headers["accept"] == "application/json"

    @pytest.mark.asyncio
    async def test_publish_http_error_with_message(
        self, uptime_kuma_publisher: uptime_kuma.UptimeKumaPublisher, publish_args: uptime_kuma.UptimeKumaPublishArgs
    ) -> None:
        """Test publish with HTTP error that includes a message (no exception raised)."""
        with respx.mock() as mock:
            mock.get(f"{publish_args.url}/api/push/test-token").respond(
                httpx.codes.NOT_FOUND, json={"ok": False, "msg": "Monitor not found or not active"}
            )
            await uptime_kuma_publisher.publish(publish_args)
            # Ensure request happened
            request = mock.calls[0][0]
            assert request.url.path == "/api/push/test-token"

    @pytest.mark.asyncio
    async def test_publish_http_error_no_message(
        self, uptime_kuma_publisher: uptime_kuma.UptimeKumaPublisher, publish_args: uptime_kuma.UptimeKumaPublishArgs
    ) -> None:
        """Test publish with HTTP error that doesn't include a message (no exception raised)."""
        with respx.mock() as mock:
            mock.get(f"{publish_args.url}/api/push/test-token").respond(
                httpx.codes.INTERNAL_SERVER_ERROR, json={"ok": False, "msg": "Internal server error"}
            )
            await uptime_kuma_publisher.publish(publish_args)
            request = mock.calls[0][0]
            assert request.url.path == "/api/push/test-token"

    @pytest.mark.asyncio
    async def test_publish_request_error(
        self, uptime_kuma_publisher: uptime_kuma.UptimeKumaPublisher, publish_args: uptime_kuma.UptimeKumaPublishArgs
    ) -> None:
        """Test publish with request error (no exception raised)."""
        with respx.mock() as mock:
            mock.get(f"{publish_args.url}/api/push/test-token").mock(side_effect=httpx.RequestError("Connection error"))
            await uptime_kuma_publisher.publish(publish_args)

    @pytest.mark.parametrize(
        ("status", "msg", "ping", "expected_params"),
        [
            ("up", "Test", 1.0, {"status": "up", "msg": "Test", "ping": "1.0"}),
            ("down", "", None, {"status": "down", "msg": ""}),
        ],
    )
    @pytest.mark.asyncio
    async def test_publish_parameters_serialization(
        self,
        uptime_kuma_publisher: uptime_kuma.UptimeKumaPublisher,
        status: Literal["up", "down"],
        msg: str,
        ping: float | None,
        expected_params: dict[str, Any],
    ) -> None:
        """Test that push parameters are correctly serialized to query params."""
        with respx.mock() as mock:
            # Create parameters and make the request
            args = uptime_kuma.UptimeKumaPublishArgs(
                url="http://ignored",
                push_token="test-token",  # noqa: S106
                status=status,
                msg=msg,
                ping=ping,
            )
            # Mock the response using the URL from args
            mock.get(f"{args.url}/api/push/test-token").respond(httpx.codes.OK, json={"ok": True})
            await uptime_kuma_publisher.publish(args)

            # Get the request that was made
            request = mock.calls[0][0]

            # Check the URL and method
            assert request.method == "GET"
            assert request.url.path == "/api/push/test-token"

            # Check that all expected parameters are present in the URL query string
            for key, expected_value in expected_params.items():
                if expected_value is not None:
                    assert request.url.params[key] == expected_value
