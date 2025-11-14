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

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, cast
from unittest import mock

import pytest

from kumacub.infrastructure import executors

if TYPE_CHECKING:
    from kumacub.infrastructure.executors import _ProcessExecutor


class TestProcessExecutor:
    """Integration tests for executors.ExecutorP with real subprocess execution."""

    @pytest.fixture
    def executor(self, monkeypatch: pytest.MonkeyPatch) -> executors.ExecutorP:
        """Return a executors.ExecutorP instance with mocked logger."""
        # Patch the logger to avoid issues with test environment
        mock_logger = mock.MagicMock()
        monkeypatch.setattr(
            "kumacub.infrastructure.executors.process_executor.structlog.get_logger", lambda: mock_logger
        )
        return executors.get_executor("process")

    @pytest.fixture
    def exec_success(self) -> executors.ProcessExecutorArgs:
        """Return executor args that will succeed."""
        return executors.ProcessExecutorArgs(name="success", command="echo", args=["-n", "test output"])

    @pytest.fixture
    def exec_fail(self) -> executors.ProcessExecutorArgs:
        """Return executor args that will fail with non-zero exit code."""
        return executors.ProcessExecutorArgs(name="fail", command="false")

    @pytest.fixture
    def exec_not_found(self) -> executors.ProcessExecutorArgs:
        """Return executor args with a non-existent command."""
        return executors.ProcessExecutorArgs(name="not_found", command="non_existent_command")

    @pytest.mark.asyncio
    async def test_run_success(
        self, executor: executors.ExecutorP, exec_success: executors.ProcessExecutorArgs
    ) -> None:
        """Test running a successful command."""
        result = cast("executors.ProcessExecutorOutput", await executor.run(args=exec_success))

        assert result.exit_code == 0
        assert result.stdout == "test output"
        assert result.stderr == ""

    @pytest.mark.asyncio
    async def test_run_error(self, executor: executors.ExecutorP, exec_fail: executors.ProcessExecutorArgs) -> None:
        """Test running a command that returns non-zero exit code."""
        result = cast("executors.ProcessExecutorOutput", await executor.run(args=exec_fail))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert result.stderr == ""

    @pytest.mark.asyncio
    async def test_run_command_not_found(
        self,
        executor: executors.ExecutorP,
        exec_not_found: executors.ProcessExecutorArgs,
    ) -> None:
        """Test running a non-existent command."""
        with pytest.raises(FileNotFoundError):
            await executor.run(args=exec_not_found)

    @pytest.mark.asyncio
    async def test_run_timeout(
        self,
        executor: executors.ExecutorP,
        exec_success: executors.ProcessExecutorArgs,
    ) -> None:
        """Test command timeout handling."""
        with (
            mock.patch.object(
                asyncio,
                "create_subprocess_exec",
                side_effect=TimeoutError("Command timed out"),
            ),
            pytest.raises(TimeoutError),
        ):
            await executor.run(args=exec_success)

    @pytest.mark.asyncio
    async def test_run_with_environment(
        self,
        executor: executors.ExecutorP,
        exec_success: executors.ProcessExecutorArgs,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test running a command with environment variables."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        exec_success.env = {"CUSTOM_VAR": "custom_value"}

        with mock.patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = mock.AsyncMock()
            mock_proc.communicate.return_value = (b"test output", b"")
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc

            await executor.run(exec_success)

            # Check that the environment variables were passed correctly
            _, kwargs = mock_exec.call_args
            env = kwargs.get("env", {})
            assert env.get("CUSTOM_VAR") == "custom_value"
            assert "TEST_VAR" not in env  # Shouldn't inherit from parent env

    @pytest.mark.asyncio
    async def test_run_with_stderr(
        self,
        executor: _ProcessExecutor,
        exec_success: executors.ProcessExecutorArgs,
    ) -> None:
        """Test running a command that writes to stderr."""
        with mock.patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = mock.AsyncMock()
            mock_proc.communicate.return_value = (b"test output", b"error message")
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc
            result = await executor.run(args=exec_success)

        assert result.exit_code == 0
        assert result.stdout == "test output"
        assert result.stderr == "error message"
