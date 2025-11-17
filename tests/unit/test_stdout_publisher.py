#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Tests for the stdout publisher."""

import json
from typing import Literal

import pytest
from _pytest.capture import CaptureFixture

from kumacub.infrastructure import publishers
from kumacub.infrastructure.publishers.stdout import StdoutPublishArgs, _StdoutPublisher


class TestStdoutPublisher:
    """Tests for the stdout publisher."""

    def test_publisher_attributes(self) -> None:
        """Test that the publisher has the correct attributes."""
        publisher = _StdoutPublisher()
        assert publisher.name == "stdout"
        assert hasattr(publisher, "publish")
        assert callable(publisher.publish)

    @pytest.mark.asyncio
    async def test_publish_success(self, capsys: CaptureFixture[str]) -> None:
        """Test publishing a message to stdout."""
        # Arrange
        args = StdoutPublishArgs(id="test_check", status="up", msg="All good")
        publisher = _StdoutPublisher()

        # Act
        await publisher.publish(args)

        # Assert
        captured = capsys.readouterr()
        output = json.loads(captured.out.strip())
        assert output == {"id": "test_check", "status": "up", "msg": "All good"}

    @pytest.mark.asyncio
    async def test_publish_default_values(self, capsys: CaptureFixture[str]) -> None:
        """Test publishing with default values."""
        # Arrange
        args = StdoutPublishArgs(id="test_check")
        publisher = _StdoutPublisher()

        # Act
        await publisher.publish(args)

        # Assert
        captured = capsys.readouterr()
        output = json.loads(captured.out.strip())
        assert output == {"id": "test_check", "status": "", "msg": ""}

    @pytest.mark.asyncio
    async def test_publish_long_message_not_truncated(self, capsys: CaptureFixture[str]) -> None:
        """Test that messages are not truncated by the publisher (truncation happens in runner)."""
        # Arrange
        message = "x" * 200  # Less than max length
        args = StdoutPublishArgs(id="test_check", msg=message)
        publisher = _StdoutPublisher()

        # Act
        await publisher.publish(args)

        # Assert
        captured = capsys.readouterr()
        output = json.loads(captured.out.strip())
        assert output["msg"] == message  # Should be unchanged


class TestStdoutPublisherIntegration:
    """Integration tests for the stdout publisher with the factory."""

    def test_get_stdout_publisher(self) -> None:
        """Test getting the stdout publisher from the factory."""
        publisher = publishers.get_publisher(name="stdout")
        assert isinstance(publisher, _StdoutPublisher)
        assert publisher.name == "stdout"

    @pytest.mark.parametrize(
        "status",
        [
            "",
            "up",
            "down",
        ],
    )
    @pytest.mark.asyncio
    async def test_publish_with_different_statuses(
        self, status: Literal["", "up", "down"], capsys: CaptureFixture[str]
    ) -> None:
        """Test publishing with different status values."""
        args = StdoutPublishArgs(id="test_check", status=status)
        publisher = _StdoutPublisher()

        await publisher.publish(args)

        captured = capsys.readouterr()
        output = json.loads(captured.out.strip())
        assert output["status"] == status
