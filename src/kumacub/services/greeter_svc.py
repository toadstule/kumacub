#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Greeter service: protocol, implementation, factory, and ping.

# TODO: This is a sample service used for demonstration. Replace/remove for your real project.

## Overview
This module demonstrates how to implement a service with the following components:
- Protocol (``GreeterSvcP``) - Defines the service interface
- Concrete implementation (``GreeterSvc``) - Implements the protocol
- Factory (``make_greeter_svc``) - Creates service instances with dependencies
- Health ping (``ping_greeter_svc``) - Verifies service availability

## Usage
- The service is registered by default in `kumacub.app.make_lifespan()`
- Configure via ``Settings.greeter.prefix`` in ``fs_overlay/etc/kumacub/config.toml``
- Override in tests by passing a custom ``register_services_fn`` to ``create_app()``
- Health checks appear in ``/api/v1/health/deep``
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from kumacub import config

if TYPE_CHECKING:  # type-only import
    import svcs


@runtime_checkable
class GreeterSvcP(Protocol):
    """Define the interface for a greeter service.

    Implement this protocol to create a custom greeter service that can be used
    with the application's dependency injection system.
    """

    def greet(self, name: str) -> str:
        """Return a greeting string for the given name.

        Args:
            name: The name to include in the greeting.

        Returns:
            A personalized greeting string.
        """


class GreeterSvc:
    """Default implementation of the greeter service.

    This implementation composes messages using a configurable prefix and service name.
    It's designed to be used as a reference for creating other services.
    """

    def __init__(self, *, prefix: str, service_name: str) -> None:
        """Initialize the greeter with configuration parameters.

        Args:
            prefix: The greeting prefix (e.g., "Hello" or "Hi").
            service_name: The name of the service to include in greetings.
        """
        self._prefix = prefix
        self._service_name = service_name

    def greet(self, name: str) -> str:
        """Generate a greeting for the specified name.

        Args:
            name: The name to include in the greeting.

        Returns:
            A formatted greeting string combining the prefix, name, and service name.
        """
        return f"{self._prefix}, {name} from {self._service_name}"


def make_greeter_svc(_container: svcs.Container) -> GreeterSvcP:
    """Create a GreeterSvc instance with dependencies from the container.

    This factory function demonstrates how to create service instances with
    dependencies resolved from the svcs container. It's registered in the
    application's lifespan to provide the GreeterSvcP protocol.

    Args:
        _container: The svcs container for dependency resolution.

    Returns:
        An instance of GreeterSvc configured with settings from the container.
    """
    settings = _container.get_abstract(config.Settings)
    # If optional GreeterSettings is present on Settings, prefer it; otherwise default.
    prefix = getattr(getattr(settings, "greeter", None), "prefix", "hello")
    return GreeterSvc(prefix=prefix, service_name=settings.service_name)


async def ping_greeter_svc(client: GreeterSvcP) -> None:
    """Verify the greeter service is responsive.

    This function is registered as a health check endpoint and will be called
    by the ``/api/v1/health/deep`` endpoint to verify the service is working.

    Args:
        client: An instance of a service implementing GreeterSvcP.

    Raises:
        Exception: If the service fails to respond as expected.
    """
    _ = client.greet("ping")
