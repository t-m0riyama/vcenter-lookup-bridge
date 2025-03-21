from fastapi import APIRouter
from vcenter_lookup_bridge.api.routes import datastores, portgroups, vms

api_router = APIRouter()
api_router.include_router(vms.router)
api_router.include_router(datastores.router)
api_router.include_router(portgroups.router)
