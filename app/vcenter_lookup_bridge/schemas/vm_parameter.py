from pydantic import BaseModel, Field
from vcenter_lookup_bridge.schemas.common import ApiResponse
from typing import List


class VmSearchSchema(BaseModel):
    """仮想マシンのクエリパラメータのスキーマ"""

    vcenter: str = Field(
        description="vCenterの名前を指定します。",
        default=None,
        example="vcenter01",
    )
    model_config = {"extra": "forbid"}


class VmListSearchSchema(BaseModel):
    """仮想マシン一覧のクエリパラメータのスキーマ"""

    vm_folders: list[str] = Field(
        description="仮想マシンフォルダの名前を指定します。",
        example=["folder1"],
        min_length=1,
    )
    offset: int = Field(
        description="仮想マシンフォルダ中の仮想マシンを取得する際の開始位置を指定します。",
        default=0,
        example=0,
        ge=0,
    )
    max_results: int = Field(
        description="仮想マシンフォルダ中の仮想マシンを取得する際の最大件数を指定します。",
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


class VmResponseSchema(BaseModel):
    """仮想マシンのレスポンススキーマ"""

    name: str = Field(
        description="仮想マシンの名前を示します。",
        example="example-vm01",
    )
    uuid: str = Field(
        description="仮想マシンのUUIDを示します。",
        example="421d0f07-b177-f71b-9723-123456789abc",
    )
    instanceUuid: str = Field(
        description="仮想マシンのインスタンスUUIDを示します。",
        example="50131f3e-4ec1-2bce-10eb-23456789abcd",
    )
    vcenter: str | None = Field(
        description="vCenter名を示します。",
        example="vcenter01",
    )
    datacenter: str = Field(
        description="仮想マシンのデータセンターを示します。",
        example="DC01",
    )
    cluster: str | None = Field(
        description="仮想マシンのクラスターを示します。",
        example="Cluster01",
    )
    esxiHostname: str | None = Field(
        description="仮想マシンのESXiホストを示します。",
        example="esxi01",
    )
    powerState: str = Field(
        description="仮想マシンの電源の状態を示します。",
        example="poweredOn",
    )
    numCpu: int = Field(
        description="仮想マシンのCPU数を示します。",
        example=2,
    )
    memorySizeMB: int = Field(
        description="仮想マシンのメモリサイズ(MB)を示します。",
        example=2048,
    )
    diskDevices: list | None = Field(
        description="仮想マシンのデバイス情報を示します。",
        example=[
            {"label": "Hard disk 1", "datastore": "ds01", "sizeGB": 200.0},
            {"label": "Hard disk 2", "datastore": "ds02", "sizeGB": 600.0},
        ],
    )
    networkDevices: list | None = Field(
        description="仮想マシンのネットワーク情報を示します。",
        example=[
            {
                "label": "Network adapter 1",
                "macAddress": "00:11:22:33:44:55",
                "portgroup": "Service Network",
                "connected": True,
                "startConnected": True,
            },
            {
                "label": "Network adapter 2",
                "macAddress": "11:11:22:33:44:00",
                "portgroup": "Management Network",
                "connected": False,
                "startConnected": False,
            },
        ],
    )
    vmFolder: str | None = Field(
        description="仮想マシンのフォルダを示します。",
        example="folder1",
    )
    vmPathName: str = Field(
        description="仮想マシンのVMXファイルのパスを示します。",
        example="[datastore01] example-vm01/nexample-vm01.vmx",
    )
    guestFullName: str = Field(
        description="仮想マシンのゲストOSの種別をフルネームを示します。",
        example="Ubuntu Linux (64-bit)",
    )
    hostname: str | None = Field(
        description="仮想マシンのホスト名を示します。",
        example="example-vm01",
    )
    ipAddress: str | None = Field(
        description="仮想マシンのIPアドレスを示します。",
        example="192.168.1.1",
    )
    template: bool = Field(
        description="仮想マシンがテンプレートかどうかを示します。",
        example=False,
    )
    hwVersion: str = Field(
        description="仮想マシンのハードウェアバージョンを示します。",
        example="vmx-15",
    )


class VmListResponseSchema(ApiResponse[List[VmResponseSchema]]):
    """仮想マシン一覧のレスポンススキーマ"""

    pass
