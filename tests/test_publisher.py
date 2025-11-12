#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Tests for the Publisher registry and factory."""

import pydantic
import pytest

import kumacub.infrastructure.publishers.publisher as publisher_mod


class DummyArgs(pydantic.BaseModel):
    """Dummy args model for testing."""

    value: int


@pytest.mark.asyncio
async def test_registry_and_factory_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Defining a subclass with publisher_type registers it and factory returns an instance."""
    # Isolate registry for this test
    monkeypatch.setattr(publisher_mod.Publisher, "_registry", {}, raising=False)

    class DummyPublisher(publisher_mod.Publisher[DummyArgs], publisher_type="dummy"):
        async def publish(self, _: DummyArgs) -> None:  # pragma: no cover - trivial
            return None

    assert "dummy" in publisher_mod.Publisher._registry
    assert publisher_mod.Publisher._registry["dummy"] is DummyPublisher

    # Factory should construct a new instance
    instance = publisher_mod.Publisher.factory("dummy")
    assert isinstance(instance, DummyPublisher)


def test_factory_unknown_type_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unknown publisher types raise ValueError with a helpful message."""
    monkeypatch.setattr(publisher_mod.Publisher, "_registry", {}, raising=False)

    with pytest.raises(ValueError, match="Unknown publisher type: nope") as exc:
        _ = publisher_mod.Publisher.factory("nope")

    assert "Unknown publisher type: nope" in str(exc.value)


def test_get_publisher_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_publisher proxies to Publisher.factory and returns an instance."""
    monkeypatch.setattr(publisher_mod.Publisher, "_registry", {}, raising=False)

    class DummyPublisher(publisher_mod.Publisher[DummyArgs], publisher_type="dummy"):
        async def publish(self, _: DummyArgs) -> None:  # pragma: no cover - trivial
            return None

    instance = publisher_mod.get_publisher("dummy")
    assert isinstance(instance, DummyPublisher)
