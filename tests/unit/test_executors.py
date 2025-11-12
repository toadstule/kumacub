#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Tests for Executors."""

import pytest

from kumacub.infrastructure import executors


class TestExecutorFactory:
    """Tests for Executor factory."""

    def test_factory(self) -> None:
        """Test that the factory returns the correct Executor."""
        with pytest.raises(ValueError, match="Unknown executor: unknown"):
            executors.get_executor(name="unknown")

        executor = executors.get_executor(name="process")
        assert executor.name == "process"
