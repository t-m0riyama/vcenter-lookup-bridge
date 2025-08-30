from pydantic import BaseModel, Field
from vcenter_lookup_bridge.schemas.common import ApiResponse
from typing import List


class EventListSearchSchema(BaseModel):
    """イベント一覧のクエリパラメータのスキーマ"""

    begin_time: str = Field(
        description="イベントが発生したと思われる時間帯の開始時間を指定します。(指定しない場合は7日前からのイベントを取得します。)",
        example="2025-08-15T08:53:00+09:00, 2025-08-15T08:53:00, 2025-08-15",
        default=None,
    )
    end_time: str = Field(
        description="イベントが発生したと思われる時間帯の終了時間を指定します。(指定しない場合は現在までのイベントを取得します。)",
        example="2025-08-15T08:53:00+09:00, 2025-08-15T08:53:00, 2025-08-15",
        default=None,
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
    vcenter: str = Field(
        description="vCenterの名前を指定します。",
        default=None,
        example="vcenter01",
    )
    model_config = {"extra": "forbid"}


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
