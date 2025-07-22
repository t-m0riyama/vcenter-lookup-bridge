import os
import uuid
import vcenter_lookup_bridge.vmware.instances as g

from typing import Annotated
from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache
from vcenter_lookup_bridge.schemas.portgroup_parameter import PortgroupListResponseSchema, PortgroupSearchSchema
from vcenter_lookup_bridge.utils.logging import Logging
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
)
@cache(expire=cache_expire_secs)
async def list_portgroups(
    search_params: Annotated[PortgroupSearchSchema, Query()],
    service_instances: object = Depends(Connector.get_service_instances),
):
    requestId = str(uuid.uuid4())
    try:
        vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations()
        portgroups = Portgroup.get_portgroups_by_tags_from_all_vcenters(
            service_instances=service_instances,
            configs=g.vcenter_configurations,
            tag_category=search_params.tag_category,
            tags=search_params.tags,
            vcenter_name=search_params.vcenter,
            requestId=requestId,
        )

        if portgroups:
            pagination = PaginationInfo(
                totalCount=len(portgroups),
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
                requestId=requestId,
            )
        else:
            # データが見つからない場合の部分成功
            return ApiResponse.create(
                results=[],
                success=False,
                message="指定した条件のポートグループ情報は見つかりませんでした。",
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=requestId,
            )
    except Exception as e:
        Logging.error(f"ポートグループ情報の一覧を取得中にエラーが発生しました({requestId}): {e}")
        raise e
