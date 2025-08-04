from fastapi import APIRouter
from fastapi_cache import FastAPICache
from vcenter_lookup_bridge.schemas.common import ApiResponse
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.utils.request_util import RequestUtil
from vcenter_lookup_bridge.schemas.admin_parameter import AdminResponseSchema
from vcenter_lookup_bridge.vmware.vcenter_ws_session_managr import VCenterWSSessionManager
import vcenter_lookup_bridge.vmware.instances as g

router = APIRouter(prefix="/admins", tags=["admins"])


@router.post(
    "/cache/flush",
    response_model=AdminResponseSchema,
    description="キャッシュ済みの全てのレスポンスをクリアします。",
)
async def flush_caches():
    request_id = RequestUtil.get_request_id()
    try:
        Logging.info(f"{request_id} キャッシュをクリアします。")
        vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations(
            configs=g.vcenter_configurations,
        )
        await FastAPICache.clear(key="*")

        return ApiResponse.create(
            results=[],
            success=True,
            message="キャッシュをクリアしました。",
            vcenterWsSessions=vcenter_ws_sessions,
            requestId=request_id,
        )
    except Exception as e:
        Logging.error(f"{request_id} キャッシュのクリア中にエラーが発生しました: {e}")
        raise e


@router.post(
    "/ws_session/reset",
    response_model=AdminResponseSchema,
    description="全てのvCenterのダウンマークをクリアします。",
)
async def reset_ws_session():
    request_id = RequestUtil.get_request_id()
    try:
        Logging.info(f"{request_id} 全てのvCenterのダウンマークをクリアします。")

        # Web Service APIの接続状態（ダウンマーク）をクリア
        redis = await VCenterWSSessionManager.initialize_async()
        vcenter_ws_sessions = await VCenterWSSessionManager.remove_all_vcenter_ws_sessions_async(
            redis=redis, configs=g.vcenter_configurations
        )

        return ApiResponse.create(
            results=[],
            success=True,
            message="全てのvCenterのダウンマークをクリアしました。",
            vcenterWsSessions=vcenter_ws_sessions,
            requestId=request_id,
        )
    except Exception as e:
        Logging.error(f"{request_id} 全てのvCenterのダウンマークをクリア中にエラーが発生しました: {e}")
        raise e
