#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Application result-translator package."""

from kumacub.application.result_translators.nagios import NagiosMapper
from kumacub.domain.protocols import ResultTranslatorP

_REGISTRY = {"nagios": NagiosMapper}


def get_result_translator(name: str) -> ResultTranslatorP:
    """Construct a result_translator by name with provided constructor args."""
    try:
        return _REGISTRY[name]()
    except KeyError as e:
        msg = f"Unknown result_translator type: {name}"
        raise ValueError(msg) from e
