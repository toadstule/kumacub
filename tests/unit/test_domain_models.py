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
            publisher=models.UptimeKumaPublisher(url="https://my_url.net", push_token=pydantic.SecretStr("test_token")),
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
            publisher=models.UptimeKumaPublisher(url="https://my_url.net", push_token=pydantic.SecretStr("test_token")),
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
                publisher=models.UptimeKumaPublisher(
                    url="https://my_url.net", push_token=pydantic.SecretStr("test_token")
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
                publisher=models.UptimeKumaPublisher(
                    url="https://my_url.net", push_token=pydantic.SecretStr("test_token")
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
            publisher=models.UptimeKumaPublisher(url="https://my_url.net", push_token=pydantic.SecretStr("test_token")),
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
    """Tests for publisher models and discriminated union validation."""

    def test_create_uptime_kuma_missing_url(self) -> None:
        """Test that UptimeKumaPublisher requires url field."""
        with pytest.raises(pydantic.ValidationError, match="url"):
            models.UptimeKumaPublisher(push_token=pydantic.SecretStr("test_token"))  # type: ignore[call-arg]

    def test_create_uptime_kuma_missing_push_token(self) -> None:
        """Test that UptimeKumaPublisher requires push_token field."""
        with pytest.raises(pydantic.ValidationError, match="push_token"):
            models.UptimeKumaPublisher(url="https://example.com")  # type: ignore[call-arg]

    def test_discriminated_union_stdout(self) -> None:
        """Test that discriminated union works for stdout publisher."""
        check = models.Check(
            name="test",
            executor=models.Executor(command="echo"),
            publisher={"name": "stdout"},  # type: ignore[arg-type]
        )
        assert isinstance(check.publisher, models.StdoutPublisher)

    def test_discriminated_union_uptime_kuma(self) -> None:
        """Test that discriminated union works for uptime_kuma publisher."""
        check = models.Check(
            name="test",
            executor=models.Executor(command="echo"),
            publisher={  # type: ignore[arg-type]
                "name": "uptime_kuma",
                "url": "https://example.com",
                "push_token": "token",
            },
        )
        assert isinstance(check.publisher, models.UptimeKumaPublisher)

    def test_default_publisher_name(self) -> None:
        """Test that publisher.name defaults to 'uptime_kuma' when not specified."""
        check = models.Check(
            name="test",
            executor=models.Executor(command="echo"),
            publisher={"url": "https://example.com", "push_token": "token"},  # type: ignore[arg-type]
        )
        assert isinstance(check.publisher, models.UptimeKumaPublisher)
        assert check.publisher.name == "uptime_kuma"
        assert check.publisher.url == "https://example.com"
