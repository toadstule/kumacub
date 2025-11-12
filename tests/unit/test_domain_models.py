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
            type="nagios",
            command="echo",
        )
        assert check.name == "test_check"
        assert check.type == "nagios"
        assert check.command == "echo"
        assert check.args == []  # Default value
        assert check.env == {}  # Default value
        assert check.interval == DEFAULT_INTERVAL  # Default value

    def test_valid_check_with_all_fields(self) -> None:
        """Test creating a check with all fields specified."""
        check = models.Check(
            name="full_check",
            type="nagios",
            command="/usr/local/bin/check_disk",
            args=["-w", "80%", "-c", "90%"],
            env={"PATH": "/usr/bin"},
            interval=30.5,
        )
        assert check.name == "full_check"
        assert check.command == "/usr/local/bin/check_disk"
        assert check.args == ["-w", "80%", "-c", "90%"]
        assert check.env == {"PATH": "/usr/bin"}
        assert check.interval == 30.5  # noqa: PLR2004

    def test_invalid_check_type(self) -> None:
        """Test that invalid check type is rejected."""
        with pytest.raises(pydantic.ValidationError) as exc_info:
            models.Check(
                name="bad_check",
                type="invalid_type",  # type: ignore[arg-type]
                command="echo",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("type",) for e in errors)

    def test_interval_must_be_positive(self) -> None:
        """Test that interval must be positive."""
        with pytest.raises(pydantic.ValidationError) as exc_info:
            models.Check(
                name="test",
                type="nagios",
                command="echo",
                interval=-1.0,
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("interval",) for e in errors)

    def test_interval_zero_invalid(self) -> None:
        """Test that zero interval is invalid."""
        with pytest.raises(pydantic.ValidationError) as exc_info:
            models.Check(
                name="test",
                type="nagios",
                command="echo",
                interval=0,
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("interval",) for e in errors)

    def test_check_serialization(self) -> None:
        """Test that Check can be serialized and deserialized."""
        original = models.Check(
            name="ser_check",
            type="nagios",
            command="test",
            args=["arg1"],
            env={"KEY": "value"},
            interval=45,
        )

        # Serialize to dict
        data = original.model_dump()

        # Deserialize back
        restored = models.Check(**data)

        assert restored.name == original.name
        assert restored.command == original.command
        assert restored.args == original.args
        assert restored.env == original.env
        assert restored.interval == original.interval


class TestCheckResultModel:
    """Tests for the CheckResult domain model."""

    def test_valid_result_minimal(self) -> None:
        """Test creating a result with minimal fields."""
        result = models.CheckResult()
        assert result.status == "up"  # Default
        assert result.msg == ""  # Default
        assert result.ping is None  # Default

    def test_valid_result_all_fields(self) -> None:
        """Test creating a result with all fields."""
        result = models.CheckResult(
            status="down",
            msg="Service is down",
            ping=42.5,
        )
        assert result.status == "down"
        assert result.msg == "Service is down"
        assert result.ping == 42.5  # noqa: PLR2004

    def test_status_empty_string_allowed(self) -> None:
        """Test that empty status string is allowed."""
        result = models.CheckResult(status="")
        assert result.status == ""

    def test_invalid_status_literal(self) -> None:
        """Test that invalid status literal is rejected."""
        with pytest.raises(pydantic.ValidationError) as exc_info:
            models.CheckResult(status="invalid")  # type: ignore[arg-type]
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("status",) for e in errors)

    def test_msg_max_length_enforced(self) -> None:
        """Test that message exceeding 250 characters is rejected."""
        with pytest.raises(pydantic.ValidationError) as exc_info:
            models.CheckResult(msg="x" * 251)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("msg",) for e in errors)

    def test_msg_exactly_250_chars_allowed(self) -> None:
        """Test that message of exactly 250 characters is allowed."""
        result = models.CheckResult(msg="x" * MAX_MSG_LENGTH)
        assert len(result.msg) == MAX_MSG_LENGTH

    def test_ping_must_be_positive(self) -> None:
        """Test that ping must be positive when provided."""
        with pytest.raises(pydantic.ValidationError) as exc_info:
            models.CheckResult(ping=-1.0)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("ping",) for e in errors)

    def test_ping_zero_invalid(self) -> None:
        """Test that zero ping is invalid."""
        with pytest.raises(pydantic.ValidationError) as exc_info:
            models.CheckResult(ping=0.0)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("ping",) for e in errors)

    def test_ping_none_allowed(self) -> None:
        """Test that None ping is allowed."""
        result = models.CheckResult(ping=None)
        assert result.ping is None

    def test_result_serialization(self) -> None:
        """Test that CheckResult can be serialized and deserialized."""
        original = models.CheckResult(
            status="down",
            msg="Test message",
            ping=123.45,
        )

        # Serialize to dict
        data = original.model_dump()

        # Deserialize back
        restored = models.CheckResult(**data)

        assert restored.status == original.status
        assert restored.msg == original.msg
        assert restored.ping == original.ping

    def test_result_json_serialization(self) -> None:
        """Test JSON serialization round-trip."""
        original = models.CheckResult(
            status="up",
            msg="All good",
            ping=50.0,
        )

        # To JSON string
        json_str = original.model_dump_json()

        # From JSON string
        restored = models.CheckResult.model_validate_json(json_str)

        assert restored.status == original.status
        assert restored.msg == original.msg
        assert restored.ping == original.ping
