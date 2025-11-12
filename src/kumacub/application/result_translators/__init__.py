#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Application result-translator package."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Final, Protocol

from .nagios import _NagiosMapper

if TYPE_CHECKING:
    import pydantic

    from kumacub.domain import models


__all__ = ["ResultTranslatorP", "get_result_translator"]


# Extend this to add new parsers.
_RESULT_TRANSLATORS: Final[list[type[ResultTranslatorP]]] = [_NagiosMapper]

_REGISTRY: Final[dict[str, type[ResultTranslatorP]]] = {p.name: p for p in _RESULT_TRANSLATORS}


class ResultTranslatorP(Protocol):
    """Translator protocol for mapping parsed models to domain models."""

    name: ClassVar[str] = ""

    @staticmethod
    def translate(parsed: pydantic.BaseModel) -> models.CheckResult:
        """Map a parser-specific model to a domain CheckResult."""


def get_result_translator(name: str) -> ResultTranslatorP:
    """Construct a result_translator by name with provided constructor args."""
    try:
        return _REGISTRY[name]()
    except KeyError as e:
        msg = f"Unknown result_translator type: {name}"
        raise ValueError(msg) from e
