#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Tests for the publisher registry (protocol-based)."""

import pytest

from kumacub.infrastructure.publishers import registry


@pytest.mark.asyncio
async def test_registry_and_factory_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Registering a factory under a name and getting it returns an instance."""
    # Isolate registry for this test
    monkeypatch.setattr(registry, "_REGISTRY", {}, raising=False)

    class DummyPublisher:
        async def publish(self, _: object) -> None:  # pragma: no cover - trivial
            return None

    registry.register_publisher("dummy", lambda: DummyPublisher())

    assert registry.list_publishers() == ["dummy"]

    # Factory should construct a new instance
    instance = registry.get_publisher("dummy")
    assert isinstance(instance, DummyPublisher)


def test_factory_unknown_type_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unknown publisher types raise ValueError with a helpful message."""
    monkeypatch.setattr(registry, "_REGISTRY", {}, raising=False)

    with pytest.raises(ValueError, match="Unknown publisher type: nope"):
        _ = registry.get_publisher("nope")


def test_list_and_get_publisher(monkeypatch: pytest.MonkeyPatch) -> None:
    """list_publishers and get_publisher operate on the registry as expected."""
    monkeypatch.setattr(registry, "_REGISTRY", {}, raising=False)

    class DummyPublisher:
        async def publish(self, _: object) -> None:  # pragma: no cover - trivial
            return None

    registry.register_publisher("dummy", lambda: DummyPublisher())
    assert registry.list_publishers() == ["dummy"]
    instance = registry.get_publisher("dummy")
    assert isinstance(instance, DummyPublisher)
