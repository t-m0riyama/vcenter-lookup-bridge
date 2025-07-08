from pydantic import BaseModel, Field


class DatastoreSearchSchema(BaseModel):
    """データストア情報のリクエストスキーマ"""

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
        description="データストア一覧を取得する際の開始位置を指定します。",
        default=0,
        example=0,
        ge=0,
    )
    max_results: int | None = Field(
        description="データストア一覧を取得する際の最大件数を指定します。",
        default=100,
        example=100,
        ge=1,
        le=1000,
    )
    model_config = {"extra": "forbid"}


class DatastoreResponseSchema(BaseModel):
    """データストア情報のレスポンススキーマ"""

    name: str = Field(
        description="データストアの名前を示します。",
        example="ds01",
    )
    vcenter: str | None = Field(
        description="vCenter名を示します。",
        example="vcenter01",
    )
    tag_category: str | None = Field(
        description="データストアに付与されているタグのカテゴリを示します。",
        example="cat1",
    )
    tags: list[str] | None = Field(
        description="データストアに付与されているタグを示します。",
        example=["tag1", "tag2"],
    )
    capacityGB: int = Field(
        description="データストアの容量(GB)を示します。",
        example=2048,
    )
    freeSpaceGB: int = Field(
        description="データストアの空き容量(GB)を示します。",
        example=512,
    )
    type: str = Field(
        description="データストアのタイプ（VMFS, NFS, ...）を示します。",
        example="VMFS",
    )
    hosts: list[str] = Field(
        description="データストアをマウント済みのESXiホストを示します。",
        example=["host-01", "host-02"],
    )
