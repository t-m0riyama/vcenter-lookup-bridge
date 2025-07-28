from pydantic import BaseModel, Field
from vcenter_lookup_bridge.schemas.common import ApiResponse
from typing import List


class VmFolderSearchSchema(BaseModel):
    """仮想マシンフォルダのクエリパラメータのスキーマ"""

    vcenter: str = Field(
        description="vCenterの名前を指定します。",
        example="vcenter01",
    )
    model_config = {"extra": "forbid"}


class VmFolderListSearchSchema(BaseModel):
    """仮想マシンフォルダ一覧のクエリパラメータのスキーマ"""

    vm_folders: list[str] = Field(
        description="仮想マシンフォルダの名前を指定します。",
        example=["folder1"],
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


class VmFolderResponseSchema(BaseModel):
    """仮想マシンフォルダのレスポンススキーマ"""

    name: str = Field(
        description="仮想マシンフォルダの名前を示します。",
        example="folder01",
    )
    vcenter: str | None = Field(
        description="vCenter名を示します。",
        example="vcenter01",
    )


class VmFolderListResponseSchema(ApiResponse[List[VmFolderResponseSchema]]):
    """仮想マシンフォルダ一覧のレスポンススキーマ"""

    pass
