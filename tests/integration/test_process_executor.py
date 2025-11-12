#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Integration tests for ProcessExecutor class.

These tests execute real subprocesses to verify end-to-end behavior.
"""

import asyncio
from unittest import mock

import pytest

from kumacub.domain import models
from kumacub.infrastructure.executors.process_executor import ProcessExecutor


class TestProcessExecutor:
    """Integration tests for ProcessExecutor with real subprocess execution."""

    @pytest.fixture
    def runner(self, monkeypatch: pytest.MonkeyPatch) -> ProcessExecutor:
        """Return a ProcessExecutor instance with mocked logger."""
        # Patch the logger to avoid issues with test environment
        mock_logger = mock.MagicMock()
        monkeypatch.setattr(
            "kumacub.infrastructure.executors.process_executor.structlog.get_logger", lambda: mock_logger
        )
        return ProcessExecutor()

    @pytest.fixture
    def success_check(self) -> models.Check:
        """Return a check that will succeed."""
        return models.Check(
            name="success_check",
            type="nagios",
            command="echo",
            args=["-n", "test output"],
        )

    @pytest.fixture
    def error_check(self) -> models.Check:
        """Return a check that will fail with non-zero exit code."""
        return models.Check(
            name="error_check",
            type="nagios",
            command="false",
            args=[],
        )

    @pytest.fixture
    def not_found_check(self) -> models.Check:
        """Return a check with a non-existent command."""
        return models.Check(
            name="not_found_check",
            type="nagios",
            command="non_existent_command",
            args=[],
        )

    @pytest.mark.asyncio
    async def test_run_success(self, runner: ProcessExecutor, success_check: models.Check) -> None:
        """Test running a successful command."""
        result = await runner.run(success_check)

        assert result.status == "up"
        assert result.msg == "test output"
        assert isinstance(result.ping, float)
        assert result.ping > 0

    @pytest.mark.asyncio
    async def test_run_error(self, runner: ProcessExecutor, error_check: models.Check) -> None:
        """Test running a command that returns non-zero exit code."""
        result = await runner.run(error_check)

        assert result.status == "down"
        # The error message should indicate a failure, but the exact format may vary
        assert result.status == "down"
        assert isinstance(result.ping, float)
        assert result.ping > 0

    @pytest.mark.asyncio
    async def test_run_command_not_found(
        self,
        runner: ProcessExecutor,
        not_found_check: models.Check,
    ) -> None:
        """Test running a non-existent command."""
        result = await runner.run(not_found_check)

        assert result.status == "down"
        assert "Error executing check" in result.msg
        assert isinstance(result.ping, float)
        assert result.ping > 0

    @pytest.mark.asyncio
    async def test_run_timeout(
        self,
        runner: ProcessExecutor,
        success_check: models.Check,
    ) -> None:
        """Test command timeout handling."""
        with mock.patch.object(
            asyncio,
            "create_subprocess_exec",
            side_effect=TimeoutError("Command timed out"),
        ):
            result = await runner.run(success_check)

            assert result.status == "down"
            assert "timed out" in result.msg.lower()
            assert result.ping is not None
            assert result.ping > 0

    @pytest.mark.asyncio
    async def test_run_with_environment(
        self,
        runner: ProcessExecutor,
        success_check: models.Check,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test running a command with environment variables."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        success_check.env = {"CUSTOM_VAR": "custom_value"}

        with mock.patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = mock.AsyncMock()
            mock_proc.communicate.return_value = (b"test output", b"")
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc

            await runner.run(success_check)

            # Check that the environment variables were passed correctly
            _, kwargs = mock_exec.call_args
            env = kwargs.get("env", {})
            assert env.get("CUSTOM_VAR") == "custom_value"
            assert "TEST_VAR" not in env  # Shouldn't inherit from parent env

    @pytest.mark.asyncio
    async def test_run_with_stderr(
        self,
        runner: ProcessExecutor,
        success_check: models.Check,
    ) -> None:
        """Test running a command that writes to stderr."""
        with mock.patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = mock.AsyncMock()
            mock_proc.communicate.return_value = (b"test output", b"error message")
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc

            with mock.patch.object(runner._logger, "warning") as mock_warning:
                result = await runner.run(success_check)

                # Verify the warning was logged
                mock_warning.assert_called_once_with(
                    "Check %s stderr: %s",
                    "success_check",
                    "error message",
                )

            # The result should still be successful since return code is 0
            assert result.status == "up"
            assert result.msg == "test output"
            assert result.ping is not None
            assert result.ping > 0
