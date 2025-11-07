#  KumaCub - Run local checks; push results to Uptime Kuma.
#  Copyright (c) 2025.
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, version 3.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with this program.
#  If not, see <https://www.gnu.org/licenses/>.

"""Version 1 API routers for KumaCub."""

import fastapi

from kumacub.api.v1 import auth, health, sample

router = fastapi.APIRouter(prefix="/v1")
router.include_router(auth.router)
router.include_router(health.router)
# TODO: Remove the sample router include and add your own API routes.
router.include_router(sample.router)
