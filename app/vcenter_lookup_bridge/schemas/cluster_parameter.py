from pydantic import BaseModel, Field
from vcenter_lookup_bridge.schemas.common import ApiResponse
from typing import List


class ClusterSearchSchema(BaseModel):
    """クラスタのクエリパラメータのスキーマ"""

    vcenter: str = Field(
        description="vCenterの名前を指定します。",
        example="vcenter01",
    )
    model_config = {"extra": "forbid"}


class ClusterListSearchSchema(BaseModel):
    """クラスタ一覧のクエリパラメータのスキーマ"""

    clusters: list[str] = Field(
        description="クラスタの名前を指定します。",
        example=["cluster1"],
        default=None,
    )
    offset: int = Field(
        description="仮想マシンフォルダを取得する際の開始位置を指定します。",
        default=0,
        example=0,
        ge=0,
    )
    max_results: int = Field(
        description="仮想マシンフォルダを取得する際の最大件数を指定します。",
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


class ClusterResponseSchema(BaseModel):
    """クラスタのレスポンススキーマ"""

    name: str = Field(
        description="仮想マシンフォルダの名前を示します。",
        example="folder01",
    )
    status: str = Field(
        description="クラスタのステータスを示します。",
        example="green",
    )
    hosts: list[str] = Field(
        description="クラスタに所属するホストの名前を示します。",
        example=["host01", "host02"],
    )
    vcenter: str | None = Field(
        description="vCenter名を示します。",
        example="vcenter01",
    )


class ClusterListResponseSchema(ApiResponse[List[ClusterResponseSchema]]):
    """クラスタ一覧のレスポンススキーマ"""

    pass
