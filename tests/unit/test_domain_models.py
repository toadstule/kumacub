#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Tests for domain models and their validation rules."""

import pydantic
import pytest

from kumacub.domain import models

# Constants for testing
DEFAULT_INTERVAL = 60
MAX_MSG_LENGTH = 250


class TestCheckModel:
    """Tests for the Check domain model."""

    def test_valid_check_minimal(self) -> None:
        """Test creating a check with minimal required fields."""
        check = models.Check(
            name="test_check",
            executor=models.Executor(command="echo"),
            parser=models.Parser(),
            publisher=models.create_publisher(
                name="uptime_kuma", url="https://my_url.net", push_token=pydantic.SecretStr("test_token")
            ),
            schedule=models.Schedule(),
        )
        assert check.name == "test_check"
        assert check.parser.name == "nagios"
        assert check.executor.command == "echo"
        assert check.executor.args == []  # Default value
        assert check.executor.env == {}  # Default value
        assert check.schedule.interval == DEFAULT_INTERVAL  # Default value

    def test_valid_check_with_all_fields(self) -> None:
        """Test creating a check with all fields specified."""
        check = models.Check(
            name="full_check",
            executor=models.Executor(
                command="/usr/local/bin/check_disk", args=["-w", "80%", "-c", "90%"], env={"PATH": "/usr/bin"}
            ),
            parser=models.Parser(),
            publisher=models.create_publisher(
                name="uptime_kuma", url="https://my_url.net", push_token=pydantic.SecretStr("test_token")
            ),
            schedule=models.Schedule(interval=30.5),
        )
        assert check.name == "full_check"
        assert check.executor.command == "/usr/local/bin/check_disk"
        assert check.executor.args == ["-w", "80%", "-c", "90%"]
        assert check.executor.env == {"PATH": "/usr/bin"}
        assert check.schedule.interval == 30.5  # noqa: PLR2004

    def test_interval_must_be_positive(self) -> None:
        """Test that interval must be positive."""
        with pytest.raises(pydantic.ValidationError) as exc_info:
            models.Check(
                name="test",
                executor=models.Executor(command="echo"),
                parser=models.Parser(),
                publisher=models.create_publisher(
                    name="uptime_kuma", url="https://my_url.net", push_token=pydantic.SecretStr("test_token")
                ),
                schedule=models.Schedule(interval=-1.0),
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("interval",) for e in errors)

    def test_interval_zero_invalid(self) -> None:
        """Test that zero interval is invalid."""
        with pytest.raises(pydantic.ValidationError) as exc_info:
            models.Check(
                name="test",
                executor=models.Executor(command="echo"),
                parser=models.Parser(),
                publisher=models.create_publisher(
                    name="uptime_kuma", url="https://my_url.net", push_token=pydantic.SecretStr("test_token")
                ),
                schedule=models.Schedule(interval=0),
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("interval",) for e in errors)

    def test_check_serialization(self) -> None:
        """Test that Check can be serialized and deserialized."""
        original = models.Check(
            name="ser_check",
            executor=models.Executor(command="test", args=["arg1"], env={"KEY": "value"}),
            parser=models.Parser(),
            publisher=models.create_publisher(
                name="uptime_kuma", url="https://my_url.net", push_token=pydantic.SecretStr("test_token")
            ),
            schedule=models.Schedule(interval=45),
        )

        # Serialize to dict
        data = original.model_dump()

        # Deserialize back
        restored = models.Check(**data)

        assert restored.name == original.name
        assert restored.executor.command == original.executor.command
        assert restored.executor.args == original.executor.args
        assert restored.executor.env == original.executor.env
        assert restored.schedule.interval == original.schedule.interval


class TestPublisherModels:
    """Tests for publisher models and factory function."""

    def test_create_stdout_publisher(self) -> None:
        """Test creating a stdout publisher with default values."""
        publisher = models.create_publisher(name="stdout")
        assert isinstance(publisher, models.StdoutPublisher)
        assert publisher.name == "stdout"
        assert publisher.url == ""
        assert publisher.push_token.get_secret_value() == ""

    def test_create_uptime_kuma_publisher(self) -> None:
        """Test creating an Uptime Kuma publisher with required fields."""
        publisher = models.create_publisher(name="uptime_kuma", url="https://example.com", push_token="test_token")  # noqa: S106
        assert isinstance(publisher, models.UptimeKumaPublisher)
        assert publisher.name == "uptime_kuma"
        assert publisher.url == "https://example.com"
        assert publisher.push_token.get_secret_value() == "test_token"

    def test_create_uptime_kuma_with_secret_str(self) -> None:
        """Test creating an Uptime Kuma publisher with SecretStr push_token."""
        secret = pydantic.SecretStr("test_secret")
        publisher = models.create_publisher(name="uptime_kuma", url="https://example.com", push_token=secret)
        assert publisher.push_token.get_secret_value() == "test_secret"

    def test_create_uptime_kuma_missing_url(self) -> None:
        """Test creating an Uptime Kuma publisher with missing URL."""
        with pytest.raises(ValueError, match="url and push_token are required for UptimeKumaPublisher"):
            models.create_publisher(name="uptime_kuma", push_token="test_token")  # noqa: S106

    def test_create_uptime_kuma_missing_push_token(self) -> None:
        """Test creating an Uptime Kuma publisher with missing push token."""
        with pytest.raises(ValueError, match="url and push_token are required for UptimeKumaPublisher"):
            models.create_publisher(name="uptime_kuma", url="https://example.com")

    def test_create_unknown_publisher(self) -> None:
        """Test creating a publisher with an unknown type."""
        with pytest.raises(ValueError, match="Unknown publisher name: unknown"):
            models.create_publisher(name="unknown")  # type: ignore[arg-type]
