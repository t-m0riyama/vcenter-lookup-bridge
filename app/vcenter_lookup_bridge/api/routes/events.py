import os

from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi_cache.decorator import cache
import vcenter_lookup_bridge.vmware.instances as g
from vcenter_lookup_bridge.schemas.common import ApiResponse, PaginationInfo
from vcenter_lookup_bridge.schemas.event_parameter import (
    EventListSearchSchema,
    EventListResponseSchema,
)
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.utils.request_util import RequestUtil
from vcenter_lookup_bridge.vmware.connector import Connector
from vcenter_lookup_bridge.vmware.vcenter_ws_session_managr import VCenterWSSessionManager
from vcenter_lookup_bridge.vmware.event import Event

# const
CACHE_EXPIRE_SECS_DEFAULT = 60

router = APIRouter(prefix="/events", tags=["events"])
cache_expire_secs = int(os.getenv("VLB_CACHE_EXPIRE_SECS", CACHE_EXPIRE_SECS_DEFAULT))


@router.get(
    "/",
    response_model=EventListResponseSchema,
    description="イベント一覧を取得します。",
    responses={
        404: {
            "description": "指定した条件のイベントが見つからない場合に返されます。",
        },
        500: {
            "description": "イベント情報の一覧を取得中にエラーが発生した場合に返されます。",
        },
    },
)
@cache(expire=cache_expire_secs)
async def list_events(
    search_params: Annotated[EventListSearchSchema, Query()],
    service_instances: object = Depends(Connector.get_service_instances),
):
    request_id = RequestUtil.get_request_id()
    try:
        Logging.info(f"{request_id} イベント一覧を取得します。")
        vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations(
            configs=g.vcenter_configurations,
        )
        events, total_event_count = Event.get_events_from_all_vcenters(
            service_instances=service_instances,
            configs=g.vcenter_configurations,
            vcenter_name=search_params.vcenter,
            begin_time=search_params.begin_time,
            end_time=search_params.end_time,
            days_ago_begin=search_params.days_ago_begin,
            days_ago_end=search_params.days_ago_end,
            hours_ago_begin=search_params.hours_ago_begin,
            hours_ago_end=search_params.hours_ago_end,
            event_types=search_params.event_types,
            event_sources=search_params.event_sources,
            user_names=search_params.user_names,
            ip_addresses=search_params.ip_addresses,
            offset=search_params.offset,
            max_results=search_params.max_results,
            request_id=request_id,
        )

        if events:
            pagination = PaginationInfo(
                totalCount=total_event_count,
                offset=search_params.offset,
                limit=search_params.max_results,
                hasNext=len(events) == search_params.max_results,
                hasPrevious=search_params.offset > 0,
            )
            return ApiResponse.create(
                results=events,
                success=True,
                message=f"{len(events)}件のイベントを取得しました。",
                pagination=pagination,
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
        else:
            # イベントが見つからない場合は404エラーを返す
            raise HTTPException(
                status_code=404,
                detail=f"指定した条件のイベントは見つかりませんでした。",
            )
    except Exception as e:
        if hasattr(e, "status_code") and e.status_code == 404:
            Logging.info(f"{request_id} イベント情報の一覧を取得中にエラーが発生しました: {e}")
        elif hasattr(e, "status_code") and e.status_code == 422:
            Logging.info(f"{request_id} パラメータの書式不正が発生しました: {e}")
        else:
            Logging.error(f"{request_id} イベント情報の一覧を取得中にエラーが発生しました: {e}")
        raise e
