#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025 Stephen T. Jibson.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Tests for parsers."""

import pytest

from kumacub.infrastructure import parsers


class TestParserFactory:
    """Tests for Parser factory."""

    def test_factory(self) -> None:
        """Test that the factory returns the correct parser."""
        with pytest.raises(ValueError, match="Unknown parser: unknown"):
            parsers.get_parser(name="unknown")

        parser = parsers.get_parser(name="nagios")
        assert parser.name == "nagios"
