from fastapi import APIRouter, Query
from fastapi import HTTPException
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
)
async def list_vcenters(
    search_params: Annotated[VCenterListSearchSchema, Query()],
):
    request_id = RequestUtil.get_request_id()
    try:
        Logging.info(f"{request_id} vCenter一覧を取得します。")
        vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations()
        configs = g.vcenter_configurations

        vcenters = VCenter.get_all_vcenters(
            configs=configs,
            vcenter_name=search_params.vcenter,
            offset=search_params.offset,
            max_results=search_params.max_results,
            request_id=request_id,
        )

        return ApiResponse.create(
            results=vcenters,
            success=True,
            message="接続先のvCenter一覧を取得しました。",
            vcenterWsSessions=vcenter_ws_sessions,
            requestId=request_id,
        )
    except HTTPException as http_exp:
        # データが見つからない場合の部分成功
        return ApiResponse.create(
            results=[],
            success=False,
            message="接続先に指定したvCenterは見つかりませんでした。",
            vcenterWsSessions=vcenter_ws_sessions,
            requestId=request_id,
        )
    except Exception as e:
        Logging.error(f"{request_id} vCenter一覧を取得中にエラーが発生しました: {e}")
        raise e
