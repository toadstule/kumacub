#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Unit tests for ProcessExecutor class.

These tests use mocked dependencies to verify orchestration logic in isolation.
"""

import asyncio
from unittest import mock

import pydantic
import pytest

from kumacub.domain import models
from kumacub.infrastructure.executors.process_executor import ProcessExecutor


class TestProcessExecutorUnit:
    """Unit tests for ProcessExecutor with mocked dependencies.

    These tests verify the executor orchestration logic without executing real subprocesses.
    """

    @pytest.fixture
    def runner(self, monkeypatch: pytest.MonkeyPatch) -> ProcessExecutor:
        """Return a ProcessExecutor instance with mocked logger."""
        mock_logger = mock.MagicMock()
        monkeypatch.setattr(
            "kumacub.infrastructure.executors.process_executor.structlog.get_logger", lambda: mock_logger
        )
        return ProcessExecutor()

    @pytest.fixture
    def sample_check(self) -> models.Check:
        """Return a sample check for testing."""
        return models.Check(
            name="test_check",
            type="nagios",
            command="test_command",
            args=["arg1", "arg2"],
            env={"VAR": "value"},
        )

    @pytest.mark.asyncio
    async def test_run_orchestration_success(self, runner: ProcessExecutor, sample_check: models.Check) -> None:
        """Test that executor properly orchestrates subprocess, parser, and translator."""
        # Mock subprocess execution
        with mock.patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = mock.AsyncMock()
            mock_proc.communicate.return_value = (b"output", b"")
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc

            # Mock parser
            with mock.patch(
                "kumacub.infrastructure.executors.process_executor.infra_parsers.get_parser"
            ) as mock_get_parser:
                mock_parser = mock.Mock()
                mock_parsed = mock.Mock(spec=pydantic.BaseModel)
                mock_parser.parse.return_value = mock_parsed
                mock_get_parser.return_value = mock_parser

                # Mock translator
                with mock.patch(
                    "kumacub.infrastructure.executors.process_executor.rt_translators.get_result_translator"
                ) as mock_get_translator:
                    mock_translator = mock.Mock()
                    expected_result = models.CheckResult(status="up", msg="All good")
                    mock_translator.translate.return_value = expected_result
                    mock_get_translator.return_value = mock_translator

                    result = await runner.run(sample_check)

                    # Verify subprocess was called with correct args
                    mock_exec.assert_called_once_with(
                        "test_command",
                        "arg1",
                        "arg2",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        env={"VAR": "value"},
                    )

                    # Verify parser was retrieved and called
                    mock_get_parser.assert_called_once_with(name="nagios")
                    mock_parser.parse.assert_called_once_with(exit_code=0, output="output")

                    # Verify translator was retrieved and called
                    mock_get_translator.assert_called_once_with(name="nagios")
                    mock_translator.translate.assert_called_once_with(parsed=mock_parsed)

                    # Verify result
                    assert result.status == "up"
                    assert result.msg == "All good"
                    assert result.ping is not None
                    assert result.ping >= 0

    @pytest.mark.asyncio
    async def test_run_subprocess_failure(self, runner: ProcessExecutor, sample_check: models.Check) -> None:
        """Test handling of subprocess failures."""
        with mock.patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = mock.AsyncMock()
            mock_proc.communicate.return_value = (b"error output", b"")
            mock_proc.returncode = 1
            mock_exec.return_value = mock_proc

            with mock.patch(
                "kumacub.infrastructure.executors.process_executor.infra_parsers.get_parser"
            ) as mock_get_parser:
                mock_parser = mock.Mock()
                mock_parsed = mock.Mock(spec=pydantic.BaseModel)
                mock_parser.parse.return_value = mock_parsed
                mock_get_parser.return_value = mock_parser

                with mock.patch(
                    "kumacub.infrastructure.executors.process_executor.rt_translators.get_result_translator"
                ) as mock_get_translator:
                    mock_translator = mock.Mock()
                    expected_result = models.CheckResult(status="down", msg="Check failed")
                    mock_translator.translate.return_value = expected_result
                    mock_get_translator.return_value = mock_translator

                    result = await runner.run(sample_check)

                    # Parser should be called with non-zero exit code
                    mock_parser.parse.assert_called_once_with(exit_code=1, output="error output")

                    # Result should reflect failure
                    assert result.status == "down"
                    assert result.ping is not None

    @pytest.mark.asyncio
    async def test_run_exception_handling(self, runner: ProcessExecutor, sample_check: models.Check) -> None:
        """Test that exceptions are caught and converted to CheckResult."""
        with mock.patch(
            "asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError("Command not found"),
        ):
            result = await runner.run(sample_check)

            assert result.status == "down"
            assert "Error executing check" in result.msg
            assert "Command not found" in result.msg
            assert result.ping is not None
            assert result.ping >= 0

    @pytest.mark.asyncio
    async def test_timer_measures_execution_time(self, runner: ProcessExecutor, sample_check: models.Check) -> None:
        """Test that timer correctly measures execution time."""
        with mock.patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = mock.AsyncMock()
            mock_proc.communicate.return_value = (b"output", b"")
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc

            with mock.patch(
                "kumacub.infrastructure.executors.process_executor.infra_parsers.get_parser"
            ) as mock_get_parser:
                mock_parser = mock.Mock()
                mock_parsed = mock.Mock(spec=pydantic.BaseModel)
                mock_parser.parse.return_value = mock_parsed
                mock_get_parser.return_value = mock_parser

                with mock.patch(
                    "kumacub.infrastructure.executors.process_executor.rt_translators.get_result_translator"
                ) as mock_get_translator:
                    mock_translator = mock.Mock()
                    mock_translator.translate.return_value = models.CheckResult(status="up")
                    mock_get_translator.return_value = mock_translator

                    # Mock time to control timer
                    with mock.patch(
                        "kumacub.infrastructure.executors.process_executor.time.time",
                        side_effect=[100.0, 100.5, 100.5],  # start, during, end
                    ):
                        result = await runner.run(sample_check)

                        # Should measure ~500ms (0.5 seconds = 500 milliseconds)
                        assert result.ping == pytest.approx(500.0, abs=1.0)

    @pytest.mark.asyncio
    async def test_stderr_logged_as_warning(self, runner: ProcessExecutor, sample_check: models.Check) -> None:
        """Test that stderr output is logged as warning."""
        with mock.patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = mock.AsyncMock()
            mock_proc.communicate.return_value = (b"output", b"warning message")
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc

            with mock.patch(
                "kumacub.infrastructure.executors.process_executor.infra_parsers.get_parser"
            ) as mock_get_parser:
                mock_parser = mock.Mock()
                mock_parser.parse.return_value = mock.Mock(spec=pydantic.BaseModel)
                mock_get_parser.return_value = mock_parser

                with mock.patch(
                    "kumacub.infrastructure.executors.process_executor.rt_translators.get_result_translator"
                ) as mock_get_translator:
                    mock_translator = mock.Mock()
                    mock_translator.translate.return_value = models.CheckResult(status="up")
                    mock_get_translator.return_value = mock_translator

                    await runner.run(sample_check)

                    # Verify logger.warning was called for stderr
                    runner._logger.warning.assert_called()
                    warning_calls = list(runner._logger.warning.call_args_list)
                    assert any("stderr" in str(call).lower() for call in warning_calls)
