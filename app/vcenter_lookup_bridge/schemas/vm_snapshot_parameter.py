from pydantic import BaseModel, Field
from vcenter_lookup_bridge.schemas.common import ApiResponse
from typing import List


class VmSnapshotSearchSchema(BaseModel):
    """仮想マシンスナップショットのクエリパラメータのスキーマ"""

    offset: int = Field(
        description="仮想マシンのスナップショットを取得する際の開始位置を指定します。",
        default=0,
        example=0,
        ge=0,
    )
    max_results: int = Field(
        description="仮想マシンのスナップショットを取得する際の最大件数を指定します。",
        default=100,
        example=100,
        ge=1,
        le=1000,
    )
    vcenter: str = Field(
        description="vCenterの名前を指定します。vCenter管理下の仮想マシン一覧を取得します。",
        default=None,
        example="vcenter01",
    )
    model_config = {"extra": "forbid"}


class VmSnapshotListSearchSchema(BaseModel):
    """仮想マシンスナップショット一覧のクエリパラメータのスキーマ"""

    vm_folders: list[str] = Field(
        description="仮想マシンフォルダの名前を指定します。",
        example=["folder1"],
        min_length=1,
    )
    offset: int = Field(
        description="仮想マシンのスナップショットを取得する際の開始位置を指定します。",
        default=0,
        example=0,
        ge=0,
    )
    max_results: int = Field(
        description="仮想マシンのスナップショットを取得する際の最大件数を指定します。",
        default=100,
        example=100,
        ge=1,
        le=1000,
    )
    vcenter: str = Field(
        description="vCenterの名前を指定します。vCenter管理下の仮想マシン一覧を取得します。",
        default=None,
        example="vcenter01",
    )
    model_config = {"extra": "forbid"}


class VmSnapshotResponseSchema(BaseModel):
    """仮想マシンスナップショットのレスポンススキーマ"""

    name: str = Field(
        description="スナップショットの名前を示します。",
        example="Snapshot 01",
    )
    id: int | None = Field(
        description="スナップショットのIDを示します。",
        example=123,
    )
    parentId: int | None = Field(
        description="スナップショットの親スナップショットのIDを示します。",
        example=12,
    )
    description: str | None = Field(
        description="スナップショットの説明を示します。",
        example="設定変更前に取得 2025/07/07",
    )
    createTime: str = Field(
        description="スナップショットの作成日時を示します。",
        example="2025/01/01 12:00:00",
    )
    hasChild: bool = Field(
        description="このスナップショットを元とした子スナップショットが存在する場合はTrue、存在しない場合はFalseがセットされます。",
        example=False,
    )
    vmName: str = Field(
        description="仮想マシンの名前を示します。",
        example="example-vm01",
    )
    vmInstanceUuid: str = Field(
        description="仮想マシンのインスタンスUUIDを示します。",
        example="50131f3e-4ec1-2bce-10eb-23456789abcd",
    )
    vmFolder: str | None = Field(
        description="仮想マシンのフォルダを示します。",
        example="folder1",
    )
    vcenter: str | None = Field(
        description="vCenter名を示します。",
        example="vcenter01",
    )
    datacenter: str = Field(
        description="仮想マシンのデータセンターを示します。",
        example="DC01",
    )


class VmSnapshotListResponseSchema(ApiResponse[List[VmSnapshotResponseSchema]]):
    """仮想マシンスナップショット一覧のレスポンススキーマ"""

    pass
