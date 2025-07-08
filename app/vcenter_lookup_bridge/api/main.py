from fastapi import APIRouter
from vcenter_lookup_bridge.api.routes import datastores, portgroups, vms, healthcheck, snapshots

api_router = APIRouter()
api_router.include_router(vms.router)
api_router.include_router(datastores.router)
api_router.include_router(portgroups.router)
api_router.include_router(healthcheck.router)
api_router.include_router(snapshots.router)
