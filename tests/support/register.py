#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Test registrar for svcs services.

Registers service factories and health pings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kumacub.services import auth_svc, greeter_svc

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from collections.abc import Callable

    import svcs


def registrar_fn() -> Callable[[svcs.Registry], None]:
    """Return a registrar callback that registers services on a Registry.

    Returns:
        A function that registers services with the provided registry.
    """

    def _register(registry: svcs.Registry) -> None:
        registry.register_factory(
            auth_svc.AuthSvcP,
            auth_svc.make_auth_svc,
            ping=auth_svc.ping_auth_svc,
        )
        registry.register_factory(
            greeter_svc.GreeterSvcP,
            greeter_svc.make_greeter_svc,
            ping=greeter_svc.ping_greeter_svc,
        )

    return _register
