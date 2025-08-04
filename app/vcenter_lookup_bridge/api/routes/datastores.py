import os
import vcenter_lookup_bridge.vmware.instances as g

from typing import Annotated
from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache
from vcenter_lookup_bridge.schemas.datastore_parameter import DatastoreListResponseSchema, DatastoreSearchSchema
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.utils.request_util import RequestUtil
from vcenter_lookup_bridge.vmware.connector import Connector
from vcenter_lookup_bridge.vmware.datastore import Datastore
from vcenter_lookup_bridge.vmware.vcenter_ws_session_managr import VCenterWSSessionManager
from vcenter_lookup_bridge.schemas.common import ApiResponse, PaginationInfo

# const
CACHE_EXPIRE_SECS_DEFAULT = 60

router = APIRouter(prefix="/datastores", tags=["datastores"])
cache_expire_secs = int(os.getenv("VLB_CACHE_EXPIRE_SECS", CACHE_EXPIRE_SECS_DEFAULT))


@router.get(
    "/",
    response_model=DatastoreListResponseSchema,
    description="タグを指定して、同タグが付与されたデータストア一覧を取得します。",
)
@cache(expire=cache_expire_secs)
async def list_datastores(
    search_params: Annotated[DatastoreSearchSchema, Query()],
    service_instances: object = Depends(Connector.get_service_instances),
):
    request_id = RequestUtil.get_request_id()
    try:
        Logging.info(
            f"{request_id} タグ({search_params.tag_category}:{search_params.tags})のデータストアを取得します。"
        )
        vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations(
            configs=g.vcenter_configurations,
        )
        datastores, total_datastore_count = Datastore.get_datastores_by_tags_from_all_vcenters(
            service_instances=service_instances,
            configs=g.vcenter_configurations,
            tag_category=search_params.tag_category,
            tags=search_params.tags,
            vcenter_name=search_params.vcenter,
            request_id=request_id,
        )
        if datastores:
            pagination = PaginationInfo(
                totalCount=total_datastore_count,
                offset=search_params.offset,
                limit=search_params.max_results,
                hasNext=len(datastores) == search_params.max_results,
                hasPrevious=search_params.offset > 0,
            )

            return ApiResponse.create(
                results=datastores,
                success=True,
                message=f"{len(datastores)}件のデータストア情報を取得しました。",
                pagination=pagination,
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
        else:
            # データが見つからない場合の部分成功
            return ApiResponse.create(
                results=[],
                success=False,
                message="指定した条件のデータストア情報は見つかりませんでした。",
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
    except Exception as e:
        Logging.error(f"ポデータストア情報の一覧を取得中にエラーが発生しました({request_id}): {e}")
        raise e
