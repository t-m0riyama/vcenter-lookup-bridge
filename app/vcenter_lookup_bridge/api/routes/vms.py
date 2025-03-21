import os
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi_cache.decorator import cache
from vcenter_lookup_bridge.schemas.vm_parameter import VmResponseSchema, VmSearchSchema
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.vmware.connector import Connector
from vcenter_lookup_bridge.vmware.vm import Vm

# const
CACHE_EXPIRE_SECS_DEFAULT = 60

router = APIRouter(prefix="/vms", tags=["vms"])
cache_expire_secs = int(
    os.getenv("VLB_CACHE_EXPIRE_SECS", CACHE_EXPIRE_SECS_DEFAULT))


@router.get('/', response_model=list[VmResponseSchema], description="仮想マシンフォルダを指定して、同フォルダ中の仮想マシン一覧を取得します。")
@cache(expire=cache_expire_secs)
async def list_vms(
    search_params: Annotated[VmSearchSchema, Query()],
    content: object = Depends(Connector.get_vmware_content),
):
    vms = Vm.get_vms_by_vm_folders(
        content=content,
        vm_folders=search_params.vm_folders,
        offset=search_params.offset,
        max_results=search_params.max_results,
    )
    return vms


@router.get('/{vm_instance_uuid}', response_model=VmResponseSchema, description="インスタンスUUIDを指定して、単一の仮想マシンの情報を取得します。")
@cache(expire=cache_expire_secs)
async def get_vm(
    vm_instance_uuid: Annotated[str, Path(description="インスタンスUUIDを指定します。※格納されている仮想マシンフォルダに関係なく、vmFolder属性はnullを返します。", example="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")],
    content: object = Depends(Connector.get_vmware_content),
):
    vm = Vm.get_vm_by_instance_uuid(
        content=content,
        instance_uuid=vm_instance_uuid
    )
    return vm
