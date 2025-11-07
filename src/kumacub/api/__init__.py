#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""API package containing FastAPI routers and response models for KubeCub.

Routers are aggregated under the `/api` prefix. Add versioned routers under `/api/vN/` and include them here.
"""

import fastapi

from kumacub.api import v1

router = fastapi.APIRouter(prefix="/api")
router.include_router(v1.router)
