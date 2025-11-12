#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Application-level mappers from infra parser models to domain models."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, ClassVar

import structlog

if TYPE_CHECKING:
    import pydantic

    from kumacub.domain import models


class ResultTranslator(abc.ABC):
    """Base mapper for converting infra parser models to domain models."""

    _registry: ClassVar[dict[str, type[ResultTranslator]]] = {}

    def __init__(self) -> None:
        """Initialize a ResultTranslator instance."""
        self._logger = structlog.get_logger()

    def __init_subclass__(cls, check_type: str, **kwargs: object) -> None:
        """Register a mapper for a specific check type."""
        super().__init_subclass__(**kwargs)
        cls._registry[check_type] = cls

    @classmethod
    def factory(cls, check_type: str) -> ResultTranslator:
        """Return a mapper for a specific check type."""
        try:
            return cls._registry[check_type]()
        except KeyError as e:
            msg = f"Unknown check type: {check_type}"
            raise ValueError(msg) from e

    @abc.abstractmethod
    def map(self, parsed: pydantic.BaseModel) -> models.CheckResult:
        """Map a parser-specific model to a domain CheckResult."""
        raise NotImplementedError  # pragma: no cover


def get_result_translator(check_type: str) -> ResultTranslator:
    """Return a ResultTranslator for a specific check type."""
    return ResultTranslator.factory(check_type)


def translate(check_type: str, parsed: pydantic.BaseModel) -> models.CheckResult:
    """Map a parser-specific model to a domain CheckResult.

    Convenience to map using an auto-constructed mapper instance.
    """
    return get_result_translator(check_type).map(parsed)
