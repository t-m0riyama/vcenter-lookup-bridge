from fastapi import APIRouter, Query, HTTPException
import vcenter_lookup_bridge.vmware.instances as g
from typing import Annotated

from vcenter_lookup_bridge.schemas.common import ApiResponse
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.utils.request_util import RequestUtil
from vcenter_lookup_bridge.schemas.vcenter_parameter import VCenterListSearchSchema, VCenterListResponseSchema
from vcenter_lookup_bridge.vmware.vcenter_ws_session_managr import VCenterWSSessionManager
from vcenter_lookup_bridge.vmware.vcenter import VCenter

router = APIRouter(prefix="/vcenters", tags=["vcenters"])


@router.get(
    "/",
    response_model=VCenterListResponseSchema,
    description="接続先のvCenter一覧を取得します。",
    responses={
        404: {
            "description": "指定した条件のvCenterが見つからない場合に返されます。",
        },
        500: {
            "description": "vCenter情報の一覧を取得中にエラーが発生した場合に返されます。",
        },
    },
)
async def list_vcenters(
    search_params: Annotated[VCenterListSearchSchema, Query()],
):
    request_id = RequestUtil.get_request_id()
    try:
        Logging.info(f"{request_id} vCenter一覧を取得します。")
        configs = g.vcenter_configurations
        vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations(
            configs=configs,
        )

        vcenters = VCenter.get_all_vcenters(
            configs=configs,
            vcenter_name=search_params.vcenter,
            offset=search_params.offset,
            max_results=search_params.max_results,
            request_id=request_id,
        )

        if len(vcenters) > 0:
            return ApiResponse.create(
                results=vcenters,
                success=True,
                message="接続先のvCenter一覧を取得しました。",
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
        else:
            # vCenterが見つからない場合は404エラーを返す
            raise HTTPException(
                status_code=404,
                detail=f"指定した条件のvCenterは見つかりませんでした。",
            )
    except Exception as e:
        Logging.error(f"{request_id} vCenter一覧を取得中にエラーが発生しました: {e}")
        raise e
