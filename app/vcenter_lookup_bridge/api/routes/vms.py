import os

from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query
from fastapi_cache.decorator import cache
import vcenter_lookup_bridge.vmware.instances as g
from vcenter_lookup_bridge.schemas.common import ApiResponse, PaginationInfo
from vcenter_lookup_bridge.schemas.vm_parameter import VmListSearchSchema, VmListResponseSchema, VmSearchSchema
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.utils.request_util import RequestUtil
from vcenter_lookup_bridge.vmware.connector import Connector
from vcenter_lookup_bridge.vmware.vcenter_ws_session_managr import VCenterWSSessionManager
from vcenter_lookup_bridge.vmware.vm import Vm

# const
CACHE_EXPIRE_SECS_DEFAULT = 60

router = APIRouter(prefix="/vms", tags=["vms"])
cache_expire_secs = int(os.getenv("VLB_CACHE_EXPIRE_SECS", CACHE_EXPIRE_SECS_DEFAULT))


@router.get(
    "/",
    response_model=VmListResponseSchema,
    description="仮想マシンフォルダを指定して、同フォルダ中の仮想マシン一覧を取得します。",
)
@cache(expire=cache_expire_secs)
async def list_vms(
    search_params: Annotated[VmListSearchSchema, Query()],
    service_instances: object = Depends(Connector.get_service_instances),
):
    request_id = RequestUtil.get_request_id()
    try:
        Logging.info(f"{request_id} 仮想マシンフォルダ({search_params.vm_folders})の仮想マシンを取得します。")
        vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations()
        vms, total_vm_count = Vm.get_vms_from_all_vcenters(
            service_instances=service_instances,
            configs=g.vcenter_configurations,
            vm_folders=search_params.vm_folders,
            vcenter_name=search_params.vcenter,
            offset=search_params.offset,
            max_results=search_params.max_results,
            request_id=request_id,
        )

        if vms:
            pagination = PaginationInfo(
                totalCount=total_vm_count,
                offset=search_params.offset,
                limit=search_params.max_results,
                hasNext=len(vms) == search_params.max_results,
                hasPrevious=search_params.offset > 0,
            )

            return ApiResponse.create(
                results=vms,
                success=True,
                message=f"{len(vms)}件の仮想マシンを取得しました。",
                pagination=pagination,
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
        else:
            # データが見つからない場合の部分成功
            return ApiResponse.create(
                results=[],
                success=False,
                message="指定した仮想マシンフォルダ中に仮想マシンは見つかりませんでした。",
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
    except Exception as e:
        Logging.error(f"仮想マシン情報の一覧を取得中にエラーが発生しました: {e}")
        raise e


@router.get(
    "/{vm_instance_uuid}",
    response_model=VmListResponseSchema,
    description="インスタンスUUIDを指定して、単一の仮想マシンの情報を取得します。",
)
@cache(expire=cache_expire_secs)
async def get_vm(
    vm_instance_uuid: Annotated[
        str,
        Path(
            description="インスタンスUUIDを指定します。※格納されている仮想マシンフォルダに関係なく、vmFolder属性はnullを返します。",
            example="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        ),
    ],
    search_params: Annotated[VmSearchSchema, Query()],
    service_instances: object = Depends(Connector.get_service_instances),
):
    request_id = RequestUtil.get_request_id()
    try:
        Logging.info(f"{request_id} インスタンスUUID({vm_instance_uuid})の仮想マシンを取得します。")
        vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations()
        vms = Vm.get_vm_by_instance_uuid_from_all_vcenters(
            vcenter_name=search_params.vcenter,
            service_instances=service_instances,
            instance_uuid=vm_instance_uuid,
            request_id=request_id,
        )
        if isinstance(vms, list) and len(vms) > 0:
            return ApiResponse.create(
                results=vms,
                success=True,
                message="仮想マシン情報を取得しました",
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
        else:
            # VMが見つからない場合
            return ApiResponse.create(
                results=[],
                success=False,
                message=f"指定されたインスタンスUUID({vm_instance_uuid})の仮想マシンが見つかりませんでした。",
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
    except Exception as e:
        Logging.error(f"{request_id} 仮想マシン情報を取得中にエラーが発生しました: {e}")
        raise e
