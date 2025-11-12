#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Tests for parsers and mappers (infra parse + app map)."""

import pytest

from kumacub.infrastructure import parsers
from kumacub.infrastructure.parsers import nagios


class TestParserList:
    """Tests for Parser list."""


class TestParserFactory:
    """Tests for Parser factory."""

    def test_factory(self) -> None:
        """Test that the factory returns the correct parser."""
        with pytest.raises(ValueError, match="Unknown parser: unknown"):
            parsers.get_parser(name="unknown")

        parser = parsers.get_parser(name="nagios")
        assert isinstance(parser, nagios.NagiosParser)


class TestNagiosParser:
    """Tests for NagiosParser class."""

    @pytest.mark.parametrize(
        ("exit_code", "expected_state"),
        [
            (0, "OK"),
            (1, "WARNING"),
            (2, "CRITICAL"),
            (3, "UNKNOWN"),
            (99, "UNKNOWN"),  # Unknown exit code
        ],
    )
    def test_exit_code_mapping(self, exit_code: int, expected_state: str) -> None:
        """Test that exit codes are correctly mapped to service states."""
        result = nagios.NagiosParser().parse(
            exit_code=exit_code,
            output="Test output",
        )
        assert result.service_state == expected_state
        assert result.exit_code == exit_code

    def test_empty_output(self) -> None:
        """Test with empty output."""
        result = nagios.NagiosParser().parse(
            exit_code=0,
            output="",
        )
        assert result.service_output == ""
        assert result.service_performance_data == ""
        assert result.long_service_output == ""

    def test_simple_output(self) -> None:
        """Test with simple output (no performance data)."""
        output = "Everything is fine"
        result = nagios.NagiosParser().parse(
            exit_code=0,
            output=output,
        )
        assert result.service_output == output
        assert result.service_performance_data == ""
        assert result.long_service_output == ""

    def test_with_performance_data(self) -> None:
        """Test with performance data in the first line."""
        output = "DISK OK - free space: 42% | /=42%;80;90"
        result = nagios.NagiosParser().parse(
            exit_code=0,
            output=output,
        )
        assert result.service_output == "DISK OK - free space: 42%"
        assert result.service_performance_data == "/=42%;80;90"

    def test_with_multiline_output(self) -> None:
        """Test with multiple lines of output."""
        output = """
        DISK WARNING - free space: 10%
        /: 10% used
        /home: 5% used
        """
        result = nagios.NagiosParser().parse(
            exit_code=1,  # WARNING
            output=output,
        )
        assert result.service_output == "DISK WARNING - free space: 10%"
        assert result.long_service_output == "/: 10% used\n/home: 5% used"
        assert result.service_performance_data == ""

    def test_with_performance_data_in_multiple_lines(self) -> None:
        """Test with performance data in multiple lines."""
        output = """
        DISK CRITICAL - free space: 95%
        /: 95% used | /=95%;80;90
        /home: 80% used | /home=80%;85;95
        Additional performance data | metric1=42;50;75 metric2=30;50;75
        """
        result = nagios.NagiosParser().parse(
            exit_code=2,  # CRITICAL
            output=output,
        )
        assert result.service_output == "DISK CRITICAL - free space: 95%"
        assert result.long_service_output == "/: 95% used\n/home: 80% used\nAdditional performance data"
        assert result.service_performance_data == "/=95%;80;90 /home=80%;85;95 metric1=42;50;75 metric2=30;50;75"

    def test_with_whitespace(self) -> None:
        """Test that whitespace is properly handled."""
        output = "  DISK OK - free space: 42%  |  /=42%;80;90  \n  /: 42% used  "
        result = nagios.NagiosParser().parse(
            exit_code=0,
            output=output,
        )
        assert result.service_output == "DISK OK - free space: 42%"
        assert result.service_performance_data == "/=42%;80;90"
        assert result.long_service_output == "/: 42% used"

    def test_from_api_spec(self) -> None:
        """Test contrived output from API spec."""
        output = """
        TEXT OUTPUT | OPTIONAL PERFDATA
        LONG TEXT LINE 1
        LONG TEXT LINE 2
        LONG TEXT LINE N | PERFDATA LINE 2
        PERFDATA LINE 3
        PERFDATA LINE N
        """

        parser = nagios.NagiosParser()
        result = parser.parse(
            exit_code=0,
            output=output,
        )
        assert result.service_output == "TEXT OUTPUT"
        assert result.service_performance_data == "OPTIONAL PERFDATA PERFDATA LINE 2 PERFDATA LINE 3 PERFDATA LINE N"
        assert result.long_service_output == "LONG TEXT LINE 1\nLONG TEXT LINE 2\nLONG TEXT LINE N"
