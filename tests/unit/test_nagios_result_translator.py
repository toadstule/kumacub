#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Tests for the Nagios result translator implementation."""

import pytest

from kumacub.application.result_translators import nagios as app_nagios
from kumacub.infrastructure.parsers import nagios as infra_nagios


class TestNagiosResultTranslator:
    """Tests for NagiosMapper translate behavior."""

    @pytest.fixture
    def translator(self) -> app_nagios.NagiosMapper:
        """Return a NagiosMapper instance."""
        return app_nagios.NagiosMapper()

    def test_translate_up_status(self, translator: app_nagios.NagiosMapper) -> None:
        """Exit code 0 should result in status 'up' and msg from service_output."""
        parsed = infra_nagios.Result(
            service_state="OK",
            exit_code=0,
            service_output="All good",
            long_service_output="",
            service_performance_data="",
        )
        result = translator.translate(parsed)
        assert result.status == "up"
        assert result.msg == "All good"

    def test_translate_down_status(self, translator: app_nagios.NagiosMapper) -> None:
        """Non-zero exit code should result in status 'down'."""
        parsed = infra_nagios.Result(
            service_state="CRITICAL",
            exit_code=2,
            service_output="Disk full",
            long_service_output="/ is 95%",
            service_performance_data="/=/95%;80;90",
        )
        result = translator.translate(parsed)
        assert result.status == "down"
        assert result.msg == "Disk full"
