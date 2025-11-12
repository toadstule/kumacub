#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Tests for `result_translator.ResultTranslator` base API."""

from __future__ import annotations

import pydantic
import pytest

import kumacub.application.result_translators.result_translator as rt
from kumacub.domain import models


class DummyParsed(pydantic.BaseModel):
    """Minimal parsed model used for testing mappers."""

    text: str


class DummyTranslator(rt.ResultTranslator, check_type="dummy"):
    """Concrete translator for tests to exercise registry and mapping."""

    def map(self, parsed: pydantic.BaseModel) -> models.CheckResult:
        """Map a parser-specific model to a domain CheckResult."""
        p = parsed  # keep name short; parsed is a BaseModel
        assert isinstance(p, DummyParsed)
        return models.CheckResult(status="up", msg=p.text)


class TestResultTranslatorFactory:
    """Tests for the ResultTranslator factory and registry."""

    def test_factory_unknown_type(self) -> None:
        """Unknown types raise ValueError with a helpful message."""
        with pytest.raises(ValueError, match="Unknown check type: unknown"):
            rt.ResultTranslator.factory("unknown")

    def test_factory_registered_type(self) -> None:
        """Factory returns a concrete subclass instance for a registered type."""
        mapper = rt.ResultTranslator.factory("dummy")
        assert isinstance(mapper, DummyTranslator)

    def test_get_mapper_helper(self) -> None:
        """get_mapper delegates to the factory and returns a translator instance."""
        mapper = rt.get_result_translator("dummy")
        assert isinstance(mapper, DummyTranslator)


class TestResultTranslatorMapHelpers:
    """Tests for translate convenience wrapper."""

    def test_translate(self) -> None:
        """Translate constructs the translator and maps the parsed model."""
        parsed = DummyParsed(text="hello")
        result = rt.translate("dummy", parsed)
        assert isinstance(result, models.CheckResult)
        assert result.status == "up"
        assert result.msg == "hello"
