#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Tests for publishers."""

import pytest

from kumacub.infrastructure import publishers
from kumacub.infrastructure.publishers import uptime_kuma


class TestPublisherFactory:
    """Tests for Publisher factory."""

    def test_factory(self) -> None:
        """Test that the factory returns the correct publisher."""
        with pytest.raises(ValueError, match="Unknown publisher: unknown"):
            publishers.get_publisher(name="unknown")

        publisher = publishers.get_publisher(name="uptime_kuma")
        assert isinstance(publisher, uptime_kuma.UptimeKumaPublisher)
