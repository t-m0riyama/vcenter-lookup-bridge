from fastapi import APIRouter, Depends
from vcenter_lookup_bridge.schemas.healthcheck_parameter import HealthcheckResponseSchema
from vcenter_lookup_bridge.schemas.common import ApiResponse
import vcenter_lookup_bridge.vmware.instances as g
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.utils.request_util import RequestUtil
from vcenter_lookup_bridge.vmware.connector import Connector
from vcenter_lookup_bridge.vmware.vcenter_ws_session_managr import VCenterWSSessionManager

router = APIRouter(prefix="/healthcheck", tags=["healthcheck"])


@router.get(
    "/",
    response_model=HealthcheckResponseSchema,
    description="サービスのステータスを返却します。",
    responses={
        500: {
            "description": "サービスのステータス確認中にエラーが発生した場合に返されます。",
        },
    },
)
async def get_service_status(
    service_instances: object = Depends(Connector.get_service_instances),
):
    request_id = RequestUtil.get_request_id()
    Logging.info(f"{request_id} サービスのステータスを取得します。")
    service_instance_status = "ok" if service_instances else "ng"
    vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations(
        configs=g.vcenter_configurations,
    )

    return ApiResponse.create(
        results={"status": "ok", "vcenter_service_instances": service_instance_status},
        success=True,
        message="サービスのステータスを取得しました",
        vcenterWsSessions=vcenter_ws_sessions,
        requestId=request_id,
    )
