from pydantic import BaseModel, Field
from vcenter_lookup_bridge.schemas.common import ApiResponse
from typing import List


class AlarmListSearchSchema(BaseModel):
    """アラーム一覧のクエリパラメータのスキーマ"""

    begin_time: str = Field(
        description="アラームが発生したと思われる時間帯の開始時間を指定します。(指定しない場合は7日前からのアラームを取得します。)",
        example="2025-08-15T08:53:00+09:00, 2025-08-15T08:53:00, 2025-08-15",
        default=None,
    )
    end_time: str = Field(
        description="アラームが発生したと思われる時間帯の終了時間を指定します。(指定しない場合は現在までのアラームを取得します。)",
        example="2025-08-15T08:53:00+09:00, 2025-08-15T08:53:00, 2025-08-15",
        default=None,
    )
    offset: int = Field(
        description="アラームを取得する際の開始位置を指定します。",
        default=0,
        example=0,
        ge=0,
    )
    max_results: int = Field(
        description="アラームを取得する際の最大件数を指定します。",
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


class AlarmResponseSchema(BaseModel):
    """アラームのレスポンススキーマ"""

    name: str | None = Field(
        description="アラームの名前を示します。",
        example="Host TPM attestation alarm",
    )
    description: str = Field(
        description="アラームの説明を示します。",
        example="Default alarm that indicates host TPM attestation failure.",
    )
    alarmSource: str | None = Field(
        description="アラームのソースを示します。",
        example="host01",
    )
    status: str = Field(
        description="アラームのステータスを示します。",
        example="red",
        enum=["red", "yellow", "green", "gray"],
    )
    createdTime: str = Field(
        description="アラームの作成時間を示します。（ISO 8601形式）",
        example="2025-08-15T8:53:00+00:00",
    )
    acknowledged: bool = Field(
        description="アラームが確認済みかどうかを示します。",
        example=False,
    )
    acknowledgedTime: str | None = Field(
        description="アラームを確認した時間を示します。（ISO 8601形式）",
        example="2025-08-15T8:53:00+00:00",
    )
    vcenter: str | None = Field(
        description="vCenter名を示します。",
        example="vcenter01",
    )
    datacenter: str | None = Field(
        description="データセンター名を示します。",
        example="datacenter01",
    )


class AlarmListResponseSchema(ApiResponse[List[AlarmResponseSchema]]):
    """アラーム一覧のレスポンススキーマ"""

    pass
