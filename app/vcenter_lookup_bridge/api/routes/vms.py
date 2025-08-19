import os

from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, HTTPException
from fastapi_cache.decorator import cache
import vcenter_lookup_bridge.vmware.instances as g
from vcenter_lookup_bridge.schemas.common import ApiResponse, PaginationInfo
from vcenter_lookup_bridge.schemas.vm_parameter import (
    VmListSearchSchema,
    VmListResponseSchema,
    VmGetResponseSchema,
    VmResponseSchema,
    VmSearchSchema,
)
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
    responses={
        404: {
            "description": "指定した仮想マシンフォルダ中に仮想マシンが見つからない場合に返されます。",
        },
        500: {
            "description": "仮想マシン情報の一覧を取得中にエラーが発生した場合に返されます。",
        },
    },
)
@cache(expire=cache_expire_secs)
async def list_vms(
    search_params: Annotated[VmListSearchSchema, Query()],
    service_instances: object = Depends(Connector.get_service_instances),
):
    request_id = RequestUtil.get_request_id()
    try:
        Logging.info(f"{request_id} 仮想マシンフォルダ({search_params.vm_folders})の仮想マシンを取得します。")
        vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations(
            configs=g.vcenter_configurations,
        )
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
            # 仮想マシンが見つからない場合は404エラーを返す
            raise HTTPException(
                status_code=404,
                detail=f"指定した仮想マシンフォルダ({search_params.vm_folders})中に仮想マシンは見つかりませんでした。",
            )
    except Exception as e:
        Logging.error(f"仮想マシン情報の一覧を取得中にエラーが発生しました: {e}")
        raise e


@router.get(
    "/{vm_instance_uuid}",
    response_model=VmGetResponseSchema,
    description="インスタンスUUIDを指定して、単一の仮想マシンの情報を取得します。",
    responses={
        404: {
            "description": "指定したインスタンスUUIDを持つ仮想マシンが見つからない場合に返されます。",
        },
        500: {
            "description": "仮想マシン情報を取得中にエラーが発生した場合に返されます",
        },
    },
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
        vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations(
            configs=g.vcenter_configurations,
        )
        vm = Vm.get_vm_by_instance_uuid_from_all_vcenters(
            vcenter_name=search_params.vcenter,
            service_instances=service_instances,
            instance_uuid=vm_instance_uuid,
            request_id=request_id,
        )
        if isinstance(vm, VmResponseSchema):
            return ApiResponse.create(
                results=vm,
                success=True,
                message="仮想マシン情報を取得しました",
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
        else:
            # 仮想マシンが見つからない場合は404エラーを返す
            raise HTTPException(
                status_code=404,
                detail=f"指定されたインスタンスUUID({vm_instance_uuid})の仮想マシンは見つかりませんでした。",
            )
    except Exception as e:
        Logging.error(f"{request_id} 仮想マシン情報を取得中にエラーが発生しました: {e}")
        raise e
