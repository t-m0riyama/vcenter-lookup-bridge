from fastapi import APIRouter, Depends
from vcenter_lookup_bridge.schemas.healthcheck_parameter import HealthcheckResponseSchema
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.vmware.connector import Connector


router = APIRouter(prefix="/healthcheck", tags=["healthcheck"])

@router.get('/', response_model=HealthcheckResponseSchema, description="サービスのステータスを返却します。")
async def get_service_status(
    content: object = Depends(Connector.get_vmware_content),
):
    vcenter_session_status = 'ok' if content else 'ng'
    return {
        "status": "ok",
        "vcenter_session_status": vcenter_session_status
    }
