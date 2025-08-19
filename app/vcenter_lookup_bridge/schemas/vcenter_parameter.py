from pydantic import BaseModel, Field
from vcenter_lookup_bridge.schemas.common import ApiResponse
from typing import List


class VCenterSearchSchema(BaseModel):
    """vCenter取得のクエリパラメータのスキーマ"""

    vcenter: str = Field(
        description="vCenterの名前を指定します。",
        example="vcenter01",
    )
    model_config = {"extra": "forbid"}


class VCenterListSearchSchema(BaseModel):
    """vCenter一覧のクエリパラメータのスキーマ"""

    offset: int = Field(
        description="vCenterを取得する際の開始位置を指定します。",
        default=0,
        example=0,
        ge=0,
    )
    max_results: int = Field(
        description="vCenterを取得する際の最大件数を指定します。",
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


class VCenterResponseSchema(BaseModel):
    """vCenterのレスポンススキーマ"""

    name: str | None = Field(
        description="vCenter名を示します。",
        example="vcenter01",
    )
    hostName: str = Field(
        description="vCenterのホスト名を示します。",
        example="vcenter01.example.com",
    )
    port: int = Field(
        description="vCenterのポート番号を示します。",
        example=443,
    )
    description: str = Field(
        description="このvCenterの説明を示します。",
        example="vcenter01の説明",
    )


class VCenterListResponseSchema(ApiResponse[List[VCenterResponseSchema]]):
    """仮想マシンフォルダ一覧のレスポンススキーマ"""

    pass
