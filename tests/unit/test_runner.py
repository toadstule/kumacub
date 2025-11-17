#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Tests for the Runner service."""

from __future__ import annotations

import asyncio
from unittest import mock

import pydantic
import pytest

from kumacub.application.services.runner import Runner
from kumacub.domain import models
from kumacub.infrastructure import publishers


class TestRunner:
    """Tests for the Runner class."""

    @pytest.fixture
    def mock_executor(self) -> mock.MagicMock:
        """Return a mock executor."""
        return mock.AsyncMock()

    @pytest.fixture
    def mock_parser(self) -> mock.MagicMock:
        """Return a mock parser."""
        return mock.MagicMock()

    @pytest.fixture
    def mock_publisher(self) -> mock.AsyncMock:
        """Return a mock publisher."""
        return mock.AsyncMock()

    @pytest.fixture
    def sample_check(self) -> models.Check:
        """Return a sample check for testing."""
        return models.Check(
            name="test-check",
            executor=models.Executor(
                command="echo",
                args=["test"],
                env={"TEST_ENV": "test"},
            ),
            publisher=models.Publisher(
                url="https://example.com",
                push_token=pydantic.SecretStr("test-token"),
            ),
        )

    @pytest.fixture
    def runner(
        self, mock_executor: mock.MagicMock, mock_parser: mock.MagicMock, mock_publisher: mock.AsyncMock
    ) -> Runner:
        """Return a Runner instance with mocked dependencies."""
        # noinspection PyTypeChecker
        return Runner(executor=mock_executor, parser=mock_parser, publisher=mock_publisher)

    @pytest.mark.asyncio
    async def test_run_success(
        self, runner: Runner, sample_check: models.Check, mock_executor: mock.MagicMock, mock_parser: mock.MagicMock
    ) -> None:
        """Test running a successful check."""
        # Setup mock executor output
        executor_output = mock.MagicMock()
        executor_output.exit_code = 0
        executor_output.stdout = "OK - test output"
        executor_output.stderr = ""
        mock_executor.run.return_value = executor_output

        # Setup mock parser output
        parser_output = mock.MagicMock()
        parser_output.exit_code = 0
        parser_output.service_output = "OK - test output"
        mock_parser.parse.return_value = parser_output

        # Run the check
        await runner.run(sample_check)

        # Verify executor was called with correct args
        mock_executor.run.assert_called_once()
        executor_args = mock_executor.run.call_args[0][0]  # First positional argument
        assert executor_args.id == sample_check.name
        assert executor_args.command == sample_check.executor.command
        assert executor_args.args == sample_check.executor.args
        assert executor_args.env == sample_check.executor.env

        # Verify parser was called with correct args
        mock_parser.parse.assert_called_once()
        parser_args = mock_parser.parse.call_args[0][0]  # First positional argument
        assert parser_args.id == sample_check.name
        assert parser_args.output == executor_output.stdout
        assert parser_args.exit_code == executor_output.exit_code

        # Verify publisher was called with correct args
        runner._publisher.publish.assert_awaited_once()  # type: ignore[attr-defined]
        publisher_args = runner._publisher.publish.await_args[1]["args"]  # type: ignore[attr-defined]
        assert publisher_args.id == sample_check.name
        assert publisher_args.url == sample_check.publisher.url
        assert publisher_args.push_token.get_secret_value() == sample_check.publisher.push_token.get_secret_value()
        assert publisher_args.status == "up"
        assert publisher_args.msg == parser_output.service_output

    @pytest.mark.asyncio
    async def test_run_failure(
        self, runner: Runner, sample_check: models.Check, mock_executor: mock.MagicMock, mock_parser: mock.MagicMock
    ) -> None:
        """Test running a failed check."""
        # Setup mock executor output with error
        executor_output = mock.MagicMock()
        executor_output.exit_code = 1
        executor_output.stdout = ""
        executor_output.stderr = "Error: something went wrong"
        mock_executor.run.return_value = executor_output

        # Setup mock parser output for error case
        parser_output = mock.MagicMock()
        parser_output.exit_code = 1
        parser_output.service_output = "CRITICAL - something went wrong"
        mock_parser.parse.return_value = parser_output

        # Run the check
        await runner.run(sample_check)

        # Verify publisher was called with error status
        publisher_args = runner._publisher.publish.await_args[1]["args"]  # type: ignore[attr-defined]
        assert publisher_args.status == "down"
        assert publisher_args.msg == parser_output.service_output

    @pytest.mark.asyncio
    async def test_timer(self, runner: Runner) -> None:
        """Test the timer functionality."""
        # First call should return 0 and set start time
        result1 = runner._timer()
        assert result1 == 0.0
        assert runner._start_time is not None

        # Second call should return time elapsed since first call
        result2 = runner._timer()
        assert result2 > 0.0

        # Third call should return time since second call
        await asyncio.sleep(0.1)
        result3 = runner._timer()
        assert result3 > 0.0
        assert result3 > result2  # Should be a very small duration

    @pytest.mark.asyncio
    async def test_run_with_stdout_publisher(
        self, runner: Runner, mock_executor: mock.MagicMock, mock_parser: mock.MagicMock
    ) -> None:
        """Test running a check with stdout publisher."""
        # Setup mock executor output
        executor_output = mock.MagicMock()
        executor_output.exit_code = 0
        executor_output.stdout = "OK - test output"
        executor_output.stderr = ""
        mock_executor.run.return_value = executor_output

        # Setup mock parser output
        parser_output = mock.MagicMock()
        parser_output.exit_code = 0
        parser_output.service_output = "OK - test output"
        mock_parser.parse.return_value = parser_output

        # Create a check with stdout publisher
        stdout_check = models.Check(
            name="stdout-check",
            executor=models.Executor(
                command="echo",
                args=["test"],
            ),
            publisher=models.Publisher(
                name="stdout",
                url="",  # Empty string is fine for stdout publisher
                push_token=pydantic.SecretStr(""),  # Empty secret is fine for stdout
            ),
        )

        # Run the check
        await runner.run(stdout_check)

        # Verify publisher was called with stdout args
        runner._publisher.publish.assert_awaited_once()  # type: ignore[attr-defined]
        publisher_args = runner._publisher.publish.await_args[1]["args"]  # type: ignore[attr-defined]
        assert publisher_args.id == stdout_check.name
        assert publisher_args.status == "up"
        assert publisher_args.msg == parser_output.service_output

    @pytest.mark.asyncio
    async def test_run_with_long_output(
        self, runner: Runner, sample_check: models.Check, mock_executor: mock.MagicMock, mock_parser: mock.MagicMock
    ) -> None:
        """Test that a long service output is properly truncated.

        Tests issue #6: https://github.com/toadstule/kumacub/issues/6
        """
        # Create a service output that's longer than 250 characters
        max_msg_len = publishers.UptimeKumaPublishArgs.model_fields["msg"].metadata[0].max_length
        long_output = "bacon " * 50
        assert len(long_output) > max_msg_len

        # Setup mock executor output
        executor_output = mock.MagicMock()
        executor_output.exit_code = 0
        executor_output.stdout = long_output
        executor_output.stderr = ""
        mock_executor.run.return_value = executor_output

        # Setup mock parser output with a long service output
        parser_output = mock.MagicMock()
        parser_output.exit_code = 0
        parser_output.service_output = long_output
        mock_parser.parse.return_value = parser_output

        await runner.run(sample_check)

        # Verify the message was truncated
        publisher_args = runner._publisher.publish.await_args[1]["args"]  # type: ignore[attr-defined]
        assert len(publisher_args.msg) <= max_msg_len
        assert publisher_args.msg.endswith("...")

    @pytest.mark.asyncio
    async def test_run_with_stdout_publisher_and_long_output(
        self, runner: Runner, mock_executor: mock.MagicMock, mock_parser: mock.MagicMock
    ) -> None:
        """Test that a long service output is properly truncated with stdout publisher."""
        # Create a service output that's longer than the max length
        max_msg_len = publishers.StdoutPublishArgs.model_fields["msg"].metadata[0].max_length
        long_output = "x" * (max_msg_len + 50)
        assert len(long_output) > max_msg_len

        # Setup mock executor output
        executor_output = mock.MagicMock()
        executor_output.exit_code = 0
        executor_output.stdout = long_output
        executor_output.stderr = ""
        mock_executor.run.return_value = executor_output

        # Setup mock parser output with a long service output
        parser_output = mock.MagicMock()
        parser_output.exit_code = 0
        parser_output.service_output = long_output
        mock_parser.parse.return_value = parser_output

        # Create a check with stdout publisher
        stdout_check = models.Check(
            name="long-stdout-check",
            executor=models.Executor(
                command="echo",
                args=["test"],
            ),
            publisher=models.Publisher(
                name="stdout",
                url="",  # Empty string is fine for stdout publisher
                push_token=pydantic.SecretStr(""),  # Empty secret is fine for stdout
            ),
        )

        # Run the check
        await runner.run(stdout_check)

        # Verify the message was truncated
        publisher_args = runner._publisher.publish.await_args[1]["args"]  # type: ignore[attr-defined]
        assert len(publisher_args.msg) <= max_msg_len
        assert publisher_args.msg.endswith("...")
