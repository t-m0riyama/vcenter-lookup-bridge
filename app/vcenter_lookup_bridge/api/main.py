from fastapi import APIRouter
from vcenter_lookup_bridge.api.routes import (
    admins,
    datastores,
    portgroups,
    vcenters,
    vms,
    vm_snapshots,
    vm_folders,
    healthcheck,
)

api_router = APIRouter()
api_router.include_router(vcenters.router)
api_router.include_router(vms.router)
api_router.include_router(datastores.router)
api_router.include_router(portgroups.router)
api_router.include_router(vm_snapshots.router)
api_router.include_router(vm_folders.router)
api_router.include_router(healthcheck.router)
api_router.include_router(admins.router)
