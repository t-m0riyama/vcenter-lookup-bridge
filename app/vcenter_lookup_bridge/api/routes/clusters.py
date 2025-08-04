import os

from typing import Annotated
from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache
import vcenter_lookup_bridge.vmware.instances as g
from vcenter_lookup_bridge.schemas.common import ApiResponse
from vcenter_lookup_bridge.schemas.cluster_parameter import (
    ClusterListSearchSchema,
    ClusterListResponseSchema,
)
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.utils.request_util import RequestUtil
from vcenter_lookup_bridge.vmware.connector import Connector
from vcenter_lookup_bridge.vmware.vcenter_ws_session_managr import VCenterWSSessionManager
from vcenter_lookup_bridge.vmware.cluster import Cluster

# const
CACHE_EXPIRE_SECS_DEFAULT = 60

router = APIRouter(prefix="/clusters", tags=["clusters"])
cache_expire_secs = int(os.getenv("VLB_CACHE_EXPIRE_SECS", CACHE_EXPIRE_SECS_DEFAULT))


@router.get(
    "/",
    response_model=ClusterListResponseSchema,
    description="クラスタ一覧を取得します。",
)
@cache(expire=cache_expire_secs)
async def list_clusters(
    search_params: Annotated[ClusterListSearchSchema, Query()],
    service_instances: object = Depends(Connector.get_service_instances),
):
    request_id = RequestUtil.get_request_id()
    try:
        Logging.info(f"{request_id} クラスタ一覧を取得します。")
        vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations(
            configs=g.vcenter_configurations,
        )
        clusters, total_cluster_count = Cluster.get_clusters_from_all_vcenters(
            service_instances=service_instances,
            configs=g.vcenter_configurations,
            cluster_names=search_params.clusters,
            vcenter_name=search_params.vcenter,
            offset=search_params.offset,
            max_results=search_params.max_results,
            request_id=request_id,
        )

        if clusters:
            return ApiResponse.create(
                results=clusters,
                success=True,
                message=f"{len(clusters)}件のクラスタを取得しました。",
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
        else:
            # データが見つからない場合の部分成功
            return ApiResponse.create(
                results=[],
                success=False,
                message="指定した条件のクラスタは見つかりませんでした。",
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
    except Exception as e:
        Logging.error(f"クラスタ情報の一覧を取得中にエラーが発生しました: {e}")
        raise e
