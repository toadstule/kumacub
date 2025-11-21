#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Tests for the translator functions."""

import pydantic
import pytest

from kumacub.application.services import translators
from kumacub.domain import models
from kumacub.infrastructure import executors, parsers


class TestExecutorToParser:
    """Tests for executor_to_parser function."""

    def test_unknown_executor_name(self) -> None:
        """Test that unknown executor name raises ValueError."""
        output = executors.ProcessExecutorOutput(
            stdout="test",
            stderr="",
            exit_code=0,
        )

        with pytest.raises(ValueError, match="No translator for fake executor -> nagios parser"):
            translators.executor_to_parser(
                executor_output=output,
                executor_name="fake",
                parser_name="nagios",
                check_id="test-check",
            )

    def test_unknown_parser_name(self) -> None:
        """Test that unknown parser name raises ValueError."""
        output = executors.ProcessExecutorOutput(
            stdout="test",
            stderr="",
            exit_code=0,
        )

        with pytest.raises(ValueError, match="No translator for process executor -> unknown parser"):
            translators.executor_to_parser(
                executor_output=output,
                executor_name="process",
                parser_name="unknown",
                check_id="test-check",
            )


class TestParserToPublisher:
    """Tests for parser_to_publisher function."""

    def test_unknown_parser_name(self) -> None:
        """Test that unknown parser name raises ValueError."""
        output = parsers.NagiosParserOutput(
            service_state="OK",
            exit_code=0,
            service_output="test",
            long_service_output="",
            service_performance_data="",
        )
        check = models.Check(
            name="test-check",
            executor=models.Executor(command="echo", args=["test"]),
            publisher=models.create_publisher(
                name="stdout",
                url="",
                push_token=pydantic.SecretStr(""),
            ),
        )

        with pytest.raises(ValueError, match="No translator for fake parser -> stdout publisher"):
            translators.parser_to_publisher(
                parser_output=output,
                parser_name="fake",
                publisher_name="stdout",
                check=check,
            )

    def test_unknown_publisher_name(self) -> None:
        """Test that unknown publisher name raises ValueError."""
        output = parsers.NagiosParserOutput(
            service_state="OK",
            exit_code=0,
            service_output="test",
            long_service_output="",
            service_performance_data="",
        )
        check = models.Check(
            name="test-check",
            executor=models.Executor(command="echo", args=["test"]),
            publisher=models.create_publisher(
                name="uptime_kuma",
                url="https://example.com",
                push_token=pydantic.SecretStr("token"),
            ),
        )

        with pytest.raises(ValueError, match="No translator for nagios parser -> unknown publisher"):
            translators.parser_to_publisher(
                parser_output=output,
                parser_name="nagios",
                publisher_name="unknown",
                check=check,
            )
