import os
import vcenter_lookup_bridge.vmware.instances as g

from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi_cache.decorator import cache
from vcenter_lookup_bridge.schemas.portgroup_parameter import PortgroupListResponseSchema, PortgroupSearchSchema
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.utils.request_util import RequestUtil
from vcenter_lookup_bridge.vmware.connector import Connector
from vcenter_lookup_bridge.vmware.portgroup import Portgroup
from vcenter_lookup_bridge.schemas.common import ApiResponse, PaginationInfo
from vcenter_lookup_bridge.vmware.vcenter_ws_session_managr import VCenterWSSessionManager

# const
CACHE_EXPIRE_SECS_DEFAULT = 60

router = APIRouter(prefix="/portgroups", tags=["portgroups"])
cache_expire_secs = int(os.getenv("VLB_CACHE_EXPIRE_SECS", CACHE_EXPIRE_SECS_DEFAULT))


@router.get(
    "/",
    response_model=PortgroupListResponseSchema,
    description="タグを指定して、同タグが付与されたポートグループ一覧を取得します。",
    responses={
        404: {
            "description": "指定したタグを持つポートグループが見つからない場合に返されます。",
        },
        500: {
            "description": "ポートグループ情報の一覧を取得中にエラーが発生した場合に返されます。",
        },
    },
)
@cache(expire=cache_expire_secs)
async def list_portgroups(
    search_params: Annotated[PortgroupSearchSchema, Query()],
    service_instances: object = Depends(Connector.get_service_instances),
):
    request_id = RequestUtil.get_request_id()
    try:
        Logging.info(
            f"{request_id} タグ({search_params.tag_category}:{search_params.tags})のポートグループを取得します。"
        )
        vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations(
            configs=g.vcenter_configurations,
        )
        portgroups, total_portgroup_count = Portgroup.get_portgroups_by_tags_from_all_vcenters(
            service_instances=service_instances,
            configs=g.vcenter_configurations,
            tag_category=search_params.tag_category,
            tags=search_params.tags,
            vcenter_name=search_params.vcenter,
            request_id=request_id,
        )

        if portgroups:
            pagination = PaginationInfo(
                totalCount=total_portgroup_count,
                offset=search_params.offset,
                limit=search_params.max_results,
                hasNext=len(portgroups) == search_params.max_results,
                hasPrevious=search_params.offset > 0,
            )

            return ApiResponse.create(
                results=portgroups,
                success=True,
                message=f"{len(portgroups)}件のポートグループ情報を取得しました。",
                pagination=pagination,
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
        else:
            # ポートグループが見つからない場合は404エラーを返す
            raise HTTPException(
                status_code=404,
                detail=f"指定した条件のポートグループ情報は見つかりませんでした。",
            )
    except Exception as e:
        Logging.error(f"{request_id} ポートグループ情報の一覧を取得中にエラーが発生しました: {e}")
        raise e
