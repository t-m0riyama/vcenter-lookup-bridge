import os

from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi_cache.decorator import cache
import vcenter_lookup_bridge.vmware.instances as g
from vcenter_lookup_bridge.schemas.common import ApiResponse, PaginationInfo
from vcenter_lookup_bridge.schemas.alarm_parameter import (
    AlarmListSearchSchema,
    AlarmListResponseSchema,
)
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.utils.request_util import RequestUtil
from vcenter_lookup_bridge.vmware.connector import Connector
from vcenter_lookup_bridge.vmware.vcenter_ws_session_managr import VCenterWSSessionManager
from vcenter_lookup_bridge.vmware.alarm import Alarm

# const
CACHE_EXPIRE_SECS_DEFAULT = 60

router = APIRouter(prefix="/alarms", tags=["alarms"])
cache_expire_secs = int(os.getenv("VLB_CACHE_EXPIRE_SECS", CACHE_EXPIRE_SECS_DEFAULT))


@router.get(
    "/",
    response_model=AlarmListResponseSchema,
    description="トリガー済みのアラーム一覧を取得します。",
    responses={
        404: {
            "description": "指定した条件のトリガー済みアラームが見つからない場合に返されます。",
        },
        500: {
            "description": "トリガー済みのアラーム情報を取得中にエラーが発生した場合に返されます。",
        },
    },
)
@cache(expire=cache_expire_secs)
async def list_alarms(
    search_params: Annotated[AlarmListSearchSchema, Query()],
    service_instances: object = Depends(Connector.get_service_instances),
):
    request_id = RequestUtil.get_request_id()
    try:
        Logging.info(f"{request_id} トリガー済みのアラーム一覧を取得します。")
        vcenter_ws_sessions = VCenterWSSessionManager.get_all_vcenter_ws_session_informations(
            configs=g.vcenter_configurations,
        )
        alarms, total_alarm_count = Alarm.get_alarms_from_all_vcenters(
            service_instances=service_instances,
            configs=g.vcenter_configurations,
            vcenter_name=search_params.vcenter,
            begin_time=search_params.begin_time,
            end_time=search_params.end_time,
            days_ago_begin=search_params.days_ago_begin,
            days_ago_end=search_params.days_ago_end,
            hours_ago_begin=search_params.hours_ago_begin,
            hours_ago_end=search_params.hours_ago_end,
            statuses=search_params.statuses,
            alarm_sources=search_params.alarm_sources,
            acknowledged=search_params.acknowledged,
            offset=search_params.offset,
            max_results=search_params.max_results,
            request_id=request_id,
        )

        if alarms:
            pagination = PaginationInfo(
                totalCount=total_alarm_count,
                offset=search_params.offset,
                limit=search_params.max_results,
                hasNext=len(alarms) == search_params.max_results,
                hasPrevious=search_params.offset > 0,
            )
            return ApiResponse.create(
                results=alarms,
                success=True,
                message=f"{len(alarms)}件のトリガー済みアラームを取得しました。",
                pagination=pagination,
                vcenterWsSessions=vcenter_ws_sessions,
                requestId=request_id,
            )
        else:
            # トリガー済みのアラームが見つからない場合は404エラーを返す
            raise HTTPException(
                status_code=404,
                detail=f"指定した条件のトリガー済みアラームは見つかりませんでした。",
            )
    except Exception as e:
        Logging.error(f"トリガー済みのアラーム情報を取得中にエラーが発生しました: {e}")
        raise e
