from pydantic import BaseModel, Field, model_validator
from vcenter_lookup_bridge.schemas.common import ApiResponse
from typing import List


class EventListSearchSchema(BaseModel):
    """イベント一覧のクエリパラメータのスキーマ"""

    begin_time: str | None = Field(
        description="イベントが発生したと思われる時間帯の開始時間を指定します。(指定しない場合は7日前からのイベントを取得します。) \\*\\_time, days_ago\\_\\*, hours_ago\\_\\* パラメータはいずれか1種類のみを指定してください。",
        example="2025-08-15T08:53:00+09:00, 2025-08-15T08:53:00, 2025-08-15",
        default=None,
    )
    end_time: str | None = Field(
        description="イベントが発生したと思われる時間帯の終了時間を指定します。(指定しない場合は現在までのイベントを取得します。) \\*\\_time, days_ago\\_\\*, hours_ago\\_\\* パラメータはいずれか1種類のみを指定してください。",
        example="2025-08-15T08:53:00+09:00, 2025-08-15T08:53:00, 2025-08-15",
        default=None,
    )
    days_ago_begin: int | None = Field(
        description="n日前以降に発生したイベントを取得します。指定した日数の過去日付で、イベントが発生したと思われる時間帯の開始日を指定します。\\*\\_time, days_ago\\_\\*, hours_ago\\_\\* パラメータはいずれか1種類のみを指定してください。",
        example=7,
        default=None,
    )
    days_ago_end: int | None = Field(
        description="n日前以前に発生したイベントを取得します。指定した日数の過去日付で、イベントが発生したと思われる時間帯の終了日を指定します。\\*\\_time, days_ago\\_\\*, hours_ago\\_\\* パラメータはいずれか1種類のみを指定してください。",
        example=3,
        default=None,
    )
    hours_ago_begin: int | None = Field(
        description="n時間前以降に発生したイベントを取得します。指定した時間数の過去で、イベントが発生したと思われる時間帯の開始時間を指定します。\\*\\_time, days_ago\\_\\*, hours_ago\\_\\* パラメータはいずれか1種類のみを指定してください。",
        example=12,
        default=None,
    )
    hours_ago_end: int | None = Field(
        description="n時間前以前に発生したイベントを取得します。指定した時間数の過去で、イベントが発生したと思われる時間帯の終了時間を指定します。\\*\\_time, days_ago\\_\\*, hours_ago\\_\\* パラメータはいずれか1種類のみを指定してください。",
        example=3,
        default=None,
    )
    event_types: List[str] | None = Field(
        description="イベントの種類を指定します。(参考. https://files.hypervisor.fr/vcEvents.html)",
        default=None,
        example="[UserLoginSessionEvent, VmCreatedEvent]",
    )
    event_sources: List[str] | None = Field(
        description="イベントのソースを指定します。",
        default=None,
        example="[host01]",
    )
    user_names: List[str] | None = Field(
        description="イベントを発生させたユーザー名を指定します。",
        default=None,
        example="[user01, user02]",
    )
    ip_addresses: List[str] | None = Field(
        description="イベントを発生させたIPアドレスを指定します。",
        default=None,
        example="[192.168.1.1, 192.168.1.2]",
    )
    offset: int = Field(
        description="イベントを取得する際の開始位置を指定します。",
        default=0,
        example=0,
        ge=0,
    )
    max_results: int = Field(
        description="イベントを取得する際の最大件数を指定します。",
        default=100,
        example=100,
        ge=1,
        le=1000,
    )
    vcenter: str | None = Field(
        description="vCenterの名前を指定します。",
        default=None,
        example="vcenter01",
    )
    model_config = {"extra": "forbid"}

    @model_validator(mode="before")
    def check_mutually_exclusive(cls, values):
        time_keys = ["begin_time", "end_time"]
        days_keys = ["days_ago_begin", "days_ago_end"]
        hours_keys = ["hours_ago_begin", "hours_ago_end"]
        time_params = [k for k in values.keys() if values[k] is not None and k in time_keys]
        days_ago_params = [k for k in values.keys() if values[k] is not None and k in days_keys]
        hours_ago_params = [k for k in values.keys() if values[k] is not None and k in hours_keys]

        if bool(len(time_params) > 0) + bool(len(days_ago_params) > 0) + bool(len(hours_ago_params) > 0) > 1:
            raise ValueError(
                "\\*\\_time, days_ago\\_\\*, hours_ago\\_\\* パラメータはいずれか1種類のみを指定してください。"
            )
        return values


class EventResponseSchema(BaseModel):
    """イベントのレスポンススキーマ"""

    message: str = Field(
        description="イベントのメッセージを示します。",
        example="event1",
    )
    createdTime: str = Field(
        description="イベントの作成時間を示します。（ISO 8601形式）",
        example="2025-08-15T8:53:00+00:00",
    )
    eventType: str = Field(
        description="イベントの種類を示します。",
        example="UserLoginSessionEvent",
    )
    eventSource: str | None = Field(
        description="イベントのソースを示します。",
        example="host01",
    )
    userName: str | None = Field(
        description="イベントを発生させたユーザー名を示します。",
        example="user01",
    )
    ipAddress: str | None = Field(
        description="イベントを発生させたIPアドレスを示します。",
        example="192.168.1.1",
    )
    vcenter: str | None = Field(
        description="vCenter名を示します。",
        example="vcenter01",
    )
    datacenter: str | None = Field(
        description="データセンター名を示します。",
        example="datacenter01",
    )


class EventListResponseSchema(ApiResponse[List[EventResponseSchema]]):
    """イベント一覧のレスポンススキーマ"""

    pass
