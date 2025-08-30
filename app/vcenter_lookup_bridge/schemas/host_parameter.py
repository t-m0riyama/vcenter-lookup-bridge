from pydantic import BaseModel, Field
from vcenter_lookup_bridge.schemas.common import ApiResponse
from typing import List, Any


class HostSearchSchema(BaseModel):
    """ESXiホストのクエリパラメータのスキーマ"""

    vcenter: str = Field(
        description="vCenterの名前を指定します。",
        example="vcenter01",
    )
    model_config = {"extra": "forbid"}


class HostListSearchSchema(BaseModel):
    """ESXiホスト一覧のクエリパラメータのスキーマ"""

    offset: int = Field(
        description="ESXiホスト一覧を取得する際の開始位置を指定します。",
        default=0,
        example=0,
        ge=0,
    )
    max_results: int = Field(
        description="ESXiホスト一覧を取得する際の最大件数を指定します。",
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


class HostResponseSchema(BaseModel):
    """ESXiホストのレスポンススキーマ"""

    name: str = Field(
        description="ESXiホストの名前(ホスト名)を示します。",
        example="esxi01",
    )
    uuid: str = Field(
        description="ESXiホストのUUIDを示します。",
        example="99999999-1234-1234-1234-999999999999",
    )
    status: str = Field(
        description="ESXiホストのステータスを示します。",
        example="green",
        enum=["green", "yellow", "red", "gray"],
    )
    esxiVersion: str = Field(
        description="ESXiホストのバージョンを示します。",
        example="8.0.3",
    )
    esxiVersionFull: str = Field(
        description="ESXiホストのビルド番号を含む、バージョンを示します。",
        example="VMware ESXi 8.0.3 build-24280767",
    )
    vcenter: str | None = Field(
        description="vCenter名を示します。",
        example="vcenter01",
    )
    datacenter: str = Field(
        description="ESXiホストのデータセンターを示します。",
        example="DC01",
    )
    cluster: str | None = Field(
        description="ESXiホストのクラスターを示します。",
        example="Cluster01",
    )
    hardwareVendor: str = Field(
        description="ESXiホストのハードウェアベンダーを示します。",
        example="Example.com, Inc.",
    )
    hardwareModel: str = Field(
        description="ESXiホストのハードウェアモデルを示します。",
        example="Example.com Server R1000",
    )
    powerState: str = Field(
        description="ESXiホストの電源の状態を示します。",
        example="poweredOn",
    )
    cpuModel: str = Field(
        description="ESXiホストのCPUモデルを示します。",
        example="Intel(R) Xeon(R) CPU @ 2.20GHz",
    )
    numCpuSockets: int = Field(
        description="ESXiホストのCPUソケット数を示します。",
        example=1,
    )
    numCpuCores: int = Field(
        description="ESXiホストのCPUコア数を示します。",
        example=32,
    )
    numCpuThreads: int = Field(
        description="ESXiホストのCPUスレッド数を示します。",
        example=64,
    )
    memorySizeMB: int = Field(
        description="ESXiホストのメモリサイズ(MB)を示します。",
        example=65536,
    )
    datastores: list | None = Field(
        description="ESXiホストのデータストア一覧を示します。",
        example=[
            {
                "name": "ds01",
                "status": "green",
                "type": "VMFS",
                "capacitySizeGB": 4096,
                "freeSpaceSizeGB": 1024,
            },
            {
                "name": "vsanDatastore",
                "status": "green",
                "type": "vsan",
                "capacitySizeGB": 85847,
                "freeSpaceSizeGB": 24956,
            },
        ],
    )
    portgroups: list | None = Field(
        description="ESXiホストのポートグループ一覧を示します。",
        example=[
            {"name": "Service Network"},
            {"name": "Management Network"},
        ],
    )
    vswitches: list | None = Field(
        description="ESXiホストのvSwitch一覧を示します。",
        example=[
            {"name": "vSwitch0"},
            {"name": "vSwitch1"},
        ],
    )
    ipAddress: str | None = Field(
        description="ESXiホストのIPアドレスを示します。※1つ目のvmknicのIPアドレスを示します。",
        example="192.168.1.1",
    )


class HostListResponseSchema(ApiResponse[List[HostResponseSchema]]):
    """ESXiホスト一覧のレスポンススキーマ"""

    pass


class HostGetResponseSchema(ApiResponse[HostResponseSchema]):
    """単一ESXiホストのレスポンススキーマ"""

    pass
