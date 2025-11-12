#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Tests for Result Translators factory."""

import pytest

from kumacub.application import result_translators
from kumacub.application.result_translators import nagios


class TestResultTranslatorFactory:
    """Tests for result translator factory."""

    def test_factory(self) -> None:
        """Test that the factory returns the correct result translator."""
        with pytest.raises(ValueError, match="Unknown result_translator type: unknown"):
            result_translators.get_result_translator(name="unknown")

        translator = result_translators.get_result_translator(name="nagios")
        assert isinstance(translator, nagios.NagiosMapper)
