import os

from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, HTTPException
from fastapi_cache.decorator import cache
import vcenter_lookup_bridge.vmware.instances as g
from vcenter_lookup_bridge.schemas.common import ApiResponse, PaginationInfo
from vcenter_lookup_bridge.schemas.host_parameter import (
    HostListSearchSchema,
    HostListResponseSchema,
    HostGetResponseSchema,
    HostDetailResponseSchema,
    HostSearchSchema,
)
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.utils.request_util import RequestUtil
from vcenter_lookup_bridge.vmware.connector import Connector
from vcenter_lookup_bridge.vmware.vcenter_ws_session_managr import VCenterWSSessionManager
from vcenter_lookup_bridge.vmware.host import Host

# const
CACHE_EXPIRE_SECS_DEFAULT = 60

router = APIRouter(prefix="/hosts", tags=["hosts"])
cache_expire_secs = int(os.getenv("VLB_CACHE_EXPIRE_SECS", CACHE_EXPIRE_SECS_DEFAULT))


@router.get(
    "/",
    response_model=HostListResponseSchema,
    description="ESXiホスト一覧を取得します。",
    responses={
        404: {
            "description": "ESXiホストが見つからない場合に返されます。",
        },
        500: {
            "description": "ESXiホスト情報の一覧を取得中にエラーが発生した場合に返されます。",
        },
    },
)
@cache(expire=cache_expire_secs)
async def list_hosts(
    search_params: Annotated[HostListSearchSchema, Query()],
    service_instances: object = Depends(Connector.get_service_instances),
):
    request_id = RequestUtil.get_request_id()
    try:
        Logging.info(f"{request_id} ESXiホスト一覧を取得します。")
        vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations(
            configs=g.vcenter_configurations,
        )
        hosts, total_host_count = Host.get_hosts_from_all_vcenters(
            service_instances=service_instances,
            configs=g.vcenter_configurations,
            vcenter_name=search_params.vcenter,
            offset=search_params.offset,
            max_results=search_params.max_results,
            request_id=request_id,
        )

        if hosts:
            pagination = PaginationInfo(
                totalCount=total_host_count,
                offset=search_params.offset,
                limit=search_params.max_results,
                hasNext=len(hosts) == search_params.max_results,
                hasPrevious=search_params.offset > 0,
            )

            return ApiResponse.create(
                results=hosts,
                success=True,
                message=f"{len(hosts)}件のESXiホストを取得しました。",
                pagination=pagination,
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
        else:
            # 仮想マシンが見つからない場合は404エラーを返す
            raise HTTPException(
                status_code=404,
                detail=f"ESXiホストは見つかりませんでした。",
            )
    except Exception as e:
        Logging.error(f"ESXiホスト情報の一覧を取得中にエラーが発生しました: {e}")
        raise e


@router.get(
    "/{host_uuid}",
    response_model=HostGetResponseSchema,
    description="ESXiホストのUUIDを指定して、単一のESXiホストの情報を取得します。",
    responses={
        404: {
            "description": "指定したESXiホストUUIDを持つESXiホストが見つからない場合に返されます。",
        },
        500: {
            "description": "ESXiホスト情報を取得中にエラーが発生した場合に返されます",
        },
    },
)
@cache(expire=cache_expire_secs)
async def get_host(
    host_uuid: Annotated[
        str,
        Path(
            description="ホストUUIDを指定します。",
            example="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        ),
    ],
    search_params: Annotated[HostSearchSchema, Query()],
    service_instances: object = Depends(Connector.get_service_instances),
):
    request_id = RequestUtil.get_request_id()
    try:
        Logging.info(f"{request_id} ホストUUID({host_uuid})のESXiホストを取得します。")
        vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations(
            configs=g.vcenter_configurations,
        )
        host = Host.get_host_by_uuid_from_all_vcenters(
            vcenter_name=search_params.vcenter,
            service_instances=service_instances,
            host_uuid=host_uuid,
            request_id=request_id,
        )
        if isinstance(host, HostDetailResponseSchema):
            return ApiResponse.create(
                results=host,
                success=True,
                message="ESXiホスト情報を取得しました",
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
        else:
            # ESXiホストが見つからない場合は404エラーを返す
            raise HTTPException(
                status_code=404,
                detail=f"指定されたホストUUID({host_uuid})のESXiホストは見つかりませんでした。",
            )
    except Exception as e:
        Logging.error(f"{request_id} ESXiホスト情報を取得中にエラーが発生しました: {e}")
        raise e
