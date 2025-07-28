import os

from typing import Annotated
from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache
import vcenter_lookup_bridge.vmware.instances as g
from vcenter_lookup_bridge.schemas.common import ApiResponse, PaginationInfo
from vcenter_lookup_bridge.schemas.vm_folder_parameter import (
    VmFolderListSearchSchema,
    VmFolderListResponseSchema,
)
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.utils.request_util import RequestUtil
from vcenter_lookup_bridge.vmware.connector import Connector
from vcenter_lookup_bridge.vmware.vcenter_ws_session_managr import VCenterWSSessionManager
from vcenter_lookup_bridge.vmware.vm_folder import VmFolder

# const
CACHE_EXPIRE_SECS_DEFAULT = 60

router = APIRouter(prefix="/vm_folders", tags=["vm_folders"])
cache_expire_secs = int(os.getenv("VLB_CACHE_EXPIRE_SECS", CACHE_EXPIRE_SECS_DEFAULT))


@router.get(
    "/",
    response_model=VmFolderListResponseSchema,
    description="仮想マシンフォルダ一覧を取得します。",
)
@cache(expire=cache_expire_secs)
async def list_vm_folders(
    search_params: Annotated[VmFolderListSearchSchema, Query()],
    service_instances: object = Depends(Connector.get_service_instances),
):
    request_id = RequestUtil.get_request_id()
    try:
        Logging.info(f"{request_id} 仮想マシンフォルダを取得します。")
        vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations()
        vm_folders, total_vm_folder_count = VmFolder.get_vm_folders_from_all_vcenters(
            service_instances=service_instances,
            configs=g.vcenter_configurations,
            vm_folders=search_params.vm_folders,
            vcenter_name=search_params.vcenter,
            offset=search_params.offset,
            max_results=search_params.max_results,
            request_id=request_id,
        )

        if vm_folders:
            pagination = PaginationInfo(
                totalCount=total_vm_folder_count,
                offset=search_params.offset,
                limit=search_params.max_results,
                hasNext=len(vm_folders) == search_params.max_results,
                hasPrevious=search_params.offset > 0,
            )

            return ApiResponse.create(
                results=vm_folders,
                success=True,
                message=f"{len(vm_folders)}件の仮想マシンフォルダを取得しました。",
                pagination=pagination,
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
        else:
            # データが見つからない場合の部分成功
            return ApiResponse.create(
                results=[],
                success=False,
                message="指定した条件の仮想マシンフォルダは見つかりませんでした。",
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
    except Exception as e:
        Logging.error(f"仮想マシンフォルダ情報の一覧を取得中にエラーが発生しました: {e}")
        raise e
