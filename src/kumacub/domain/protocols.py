#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.
"""KumaCub domain protocols."""

from typing import Protocol

import pydantic

from kumacub.domain import models


class ResultTranslatorP(Protocol):
    """Translator protocol for mapping parsed models to domain models."""

    def translate(self, parsed: pydantic.BaseModel) -> models.CheckResult:
        """Map a parser-specific model to a domain CheckResult."""
