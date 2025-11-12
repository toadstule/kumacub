#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Nagios mapper: convert infra parser results to domain CheckResult."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast

if TYPE_CHECKING:
    import pydantic

from kumacub.domain import models
from kumacub.infrastructure import parsers  # noqa: TC001


class _NagiosMapper:
    """Map infrastructure Nagios parser Result to domain CheckResult."""

    name: ClassVar[str] = "nagios"

    @staticmethod
    def translate(parsed: pydantic.BaseModel) -> models.CheckResult:
        """Map a parser-specific model to a domain CheckResult."""
        r = cast("parsers.NagiosParserOutput", parsed)
        return models.CheckResult(
            status="up" if r.exit_code == 0 else "down",
            msg=r.service_output,
        )
