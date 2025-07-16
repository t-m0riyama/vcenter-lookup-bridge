from pydantic import BaseModel, Field
from vcenter_lookup_bridge.schemas.common import ApiResponse
from typing import List


class PortgroupSearchSchema(BaseModel):
    """ポートグループのクエリパラメータのスキーマ"""

    tag_category: str = Field(
        description="タグのカテゴリを指定します。",
        example="cat1",
        min_length=1,
    )
    tags: list[str] = Field(
        description="タグの名前を指定します。",
        example=["tag1"],
        min_length=1,
    )
    offset: int | None = Field(
        description="ポートグループ一覧を取得する際の開始位置を指定します。",
        default=0,
        example=0,
        ge=0,
    )
    max_results: int | None = Field(
        description="ポートグループ一覧を取得する際の最大件数を指定します。",
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


class PortgroupResponseSchema(BaseModel):
    """ポートグループのレスポンススキーマ"""

    name: str = Field(
        description="ポートグループの名前を示します。",
        example="pg01",
    )
    vcenter: str | None = Field(
        description="vCenter名を示します。",
        example="vcenter01",
    )
    tag_category: str | None = Field(
        description="ポートグループに付与されているタグのカテゴリを示します。",
        example="cat1",
    )
    tags: list[str] | None = Field(
        description="ポートグループに付与されているタグを示します。",
        example=["tag1", "tag2"],
    )
    hosts: list[str] | None = Field(
        description="ポートグループを利用可能なESXiホストを示します。",
        example=["host-01", "host-02"],
    )


class PortgroupListResponseSchema(ApiResponse[List[PortgroupResponseSchema]]):
    """ポートグループ一覧のレスポンススキーマ"""

    pass
