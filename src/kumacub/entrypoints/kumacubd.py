#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Console entrypoint to run the FastAPI server for KumaCub.

Usage:
    $ kumacubd

Notes:
- Reads settings from `kumacub.config.get_settings()` (env > TOML). You can set
  `CONFIG` to point at a TOML file (see `fs_overlay/etc/kumacub/config.toml`).
- Calls `configure_logging(level, structured)`; toggle console logs via
  `LOG__STRUCTURED=false` for local development.
"""

from __future__ import annotations

import uvicorn

from kumacub import config
from kumacub.logging_config import configure_logging


def main() -> None:
    """Run the FastAPI application using uvicorn."""
    settings = config.get_settings()
    configure_logging(level=settings.log.level, structured=settings.log.structured)
    uvicorn.run(
        "kumacub.app:app",
        host=settings.http_server.host,
        port=settings.http_server.port,
        reload=settings.http_server.reload,
        log_level=settings.log.level.lower(),
        log_config=None,
        access_log=False,
        factory=False,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
