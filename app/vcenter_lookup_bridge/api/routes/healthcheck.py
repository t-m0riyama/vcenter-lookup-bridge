from fastapi import APIRouter, Depends
from vcenter_lookup_bridge.schemas.healthcheck_parameter import HealthcheckResponseSchema
from vcenter_lookup_bridge.schemas.common import ApiResponse
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.vmware.connector import Connector


router = APIRouter(prefix="/healthcheck", tags=["healthcheck"])


@router.get(
    "/",
    response_model=HealthcheckResponseSchema,
    description="サービスのステータスを返却します。",
)
async def get_service_status(
    service_instances: object = Depends(Connector.get_service_instances),
):
    vcenter_session_status = "ok" if service_instances else "ng"

    return ApiResponse.create(
        results={"status": "ok", "vcenter_session_status": vcenter_session_status},
        success=True,
        message="サービスのステータスを取得しました",
    )
