from pydantic import BaseModel, Field, model_validator
from vcenter_lookup_bridge.schemas.common import ApiResponse
from typing import List


class AlarmListSearchSchema(BaseModel):
    """アラーム一覧のクエリパラメータのスキーマ"""

    begin_time: str | None = Field(
        description="アラームが発生したと思われる時間帯の開始時間を指定します。(指定しない場合は7日前からのアラームを取得します。) \\*\\_time, days_ago\\_\\*, hours_ago\\_\\* パラメータはいずれか1種類のみを指定してください。",
        example="2025-08-15T08:53:00+09:00, 2025-08-15T08:53:00, 2025-08-15",
        default=None,
    )
    end_time: str | None = Field(
        description="アラームが発生したと思われる時間帯の終了時間を指定します。(指定しない場合は現在までのアラームを取得します。) \\*\\_time, days_ago\\_\\*, hours_ago\\_\\* パラメータはいずれか1種類のみを指定してください。",
        example="2025-08-15T08:53:00+09:00, 2025-08-15T08:53:00, 2025-08-15",
        default=None,
    )
    days_ago_begin: int | None = Field(
        description="n日前以降に発生したアラームを取得します。指定した日数の過去日付で、アラームが発生したと思われる時間帯の開始日を指定します。\\*\\_time, days_ago\\_\\*, hours_ago\\_\\* パラメータはいずれか1種類のみを指定してください。",
        example=7,
        default=None,
        ge=1,
    )
    days_ago_end: int | None = Field(
        description="n日前以前に発生したアラームを取得します。指定した日数の過去日付で、アラームが発生したと思われる時間帯の終了日を指定します。\\*\\_time, days_ago\\_\\*, hours_ago\\_\\* パラメータはいずれか1種類のみを指定してください。",
        example=3,
        default=None,
        ge=0,
    )
    hours_ago_begin: int | None = Field(
        description="n時間前以降に発生したアラームを取得します。指定した時間数の過去で、アラームが発生したと思われる時間帯の開始時間を指定します。\\*\\_time, days_ago\\_\\*, hours_ago\\_\\* パラメータはいずれか1種類のみを指定してください。",
        example=12,
        default=None,
        ge=1,
    )
    hours_ago_end: int | None = Field(
        description="n時間前以前に発生したアラームを取得します。指定した時間数の過去で、アラームが発生したと思われる時間帯の終了時間を指定します。\\*\\_time, days_ago\\_\\*, hours_ago\\_\\* パラメータはいずれか1種類のみを指定してください。",
        example=3,
        default=None,
        ge=0,
    )
    statuses: List[str] | None = Field(
        description="アラームのステータスを指定します。",
        default=None,
        example=["red", "yellow"],
        enum=["red", "yellow", "green", "gray"],
    )
    alarm_sources: List[str] | None = Field(
        description="アラームのソースを指定します。",
        default=None,
        example=["host01"],
    )
    acknowledged: bool | None = Field(
        description="アラームが確認済みかどうかを指定します。",
        default=None,
        example=False,
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
