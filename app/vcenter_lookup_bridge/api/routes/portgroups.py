import os
from typing import Annotated

import vcenter_lookup_bridge.vmware.instances as g
from fastapi import APIRouter, Depends, Path, Query
from fastapi_cache.decorator import cache
from vcenter_lookup_bridge.schemas.portgroup_parameter import PortgroupResponseSchema, PortgroupSearchSchema
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.vmware.connector import Connector
from vcenter_lookup_bridge.vmware.portgroup import Portgroup

# const
CACHE_EXPIRE_SECS_DEFAULT = 60

router = APIRouter(prefix="/portgroups", tags=["portgroups"])
cache_expire_secs = int(
    os.getenv("VLB_CACHE_EXPIRE_SECS", CACHE_EXPIRE_SECS_DEFAULT))


@router.get('/', response_model=list[PortgroupResponseSchema], description="タグを指定して、同タグが付与されたポートグループ一覧を取得します。")
@cache(expire=cache_expire_secs)
async def list_portgroups(
    search_params: Annotated[PortgroupSearchSchema, Query()],
    content: object = Depends(Connector.get_vmware_content),
):
    portgroups = Portgroup.get_portgroups_by_tags(
        content=content,
        tag_category=search_params.tag_category,
        tags=search_params.tags,
    )

    return portgroups
