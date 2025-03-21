import os
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi_cache.decorator import cache
from vcenter_lookup_bridge.schemas.datastore_parameter import DatastoreResponseSchema, DatastoreSearchSchema
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.vmware.connector import Connector
from vcenter_lookup_bridge.vmware.datastore import Datastore

# const
CACHE_EXPIRE_SECS_DEFAULT = 60

router = APIRouter(prefix="/datastores", tags=["datastores"])
cache_expire_secs = int(
    os.getenv("VLB_CACHE_EXPIRE_SECS", CACHE_EXPIRE_SECS_DEFAULT))


@router.get('/', response_model=list[DatastoreResponseSchema], description="タグを指定して、同タグが付与されたデータストア一覧を取得します。")
@cache(expire=cache_expire_secs)
async def list_datastores(
    search_params: Annotated[DatastoreSearchSchema, Query()],
    content: object = Depends(Connector.get_vmware_content),
):
    return Datastore.get_datastores_by_tags(
        content=content,
        tag_category=search_params.tag_category,
        tags=search_params.tags,
    )
