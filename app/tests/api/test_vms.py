import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pyVmomi import vim

# アプリケーションのルートディレクトリをPythonパスに追加
app_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, app_root)

from main import app
from tests.api.test_helpers import MockFactory
from vcenter_lookup_bridge.vmware.connector import Connector
from vcenter_lookup_bridge.vmware.vm import Vm

client = TestClient(app)


@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def mock_datacenter():
    """データセンターのモックを作成"""
    mock = Mock()
    mock.name = "test-datacenter"
    return mock

@pytest.fixture
def mock_content(mock_datacenter):
    """コンテンツのモックを作成"""
    mock = Mock()
    mock.rootFolder = Mock()
    mock.rootFolder.childEntity = [mock_datacenter]
    mock.viewManager = Mock()
    mock.searchIndex = Mock()
    return mock

@pytest.fixture
def mock_cluster():
    """クラスターのモックを作成"""
    mock = Mock()
    mock.name = "test-cluster"
    return mock

@pytest.fixture
def mock_disk():
    """ディスクのモックを設定"""
    mock = Mock(spec=vim.vm.device.VirtualDisk)
    mock.deviceInfo = Mock()
    mock.deviceInfo.label = "Hard disk 1"
    mock.backing = Mock()
    mock.backing.fileName = "[test-datastore] test-vm/test-vm.vmdk"
    mock.backing.datastore = Mock()
    mock.backing.datastore.name = "test-datastore"
    mock.capacityInKB = 10485760  # 10GB in KB
    return mock

@pytest.fixture
def mock_network():
    """ネットワークのモックを設定"""
    mock = Mock(spec=vim.vm.device.VirtualVmxnet3)
    mock.deviceInfo = Mock()
    mock.deviceInfo.label = "Network adapter 1"
    mock.deviceInfo.summary = "VM Network"
    mock.macAddress = "00:50:56:a3:b4:c5"
    mock.backing = Mock()
    mock.backing.deviceName = "test-portgroup"
    mock.connectable = Mock()
    mock.connectable.connected = True
    mock.connectable.startConnected = True
    return mock

@pytest.fixture
def mock_guest():
    """ゲストOSのモックを設定"""
    mock = Mock()
    mock.guestFamily = "linuxGuest"
    mock.guestFullName = "Red Hat Enterprise Linux 8 (64-bit)"
    mock.guestId = "rhel8_64Guest"
    mock.guestState = "running"
    mock.hostName = "test-vm"
    mock.ipAddress = "192.168.1.100"
    return mock

@pytest.fixture
def mock_vm(mock_datacenter, mock_cluster, mock_disk, mock_network, mock_guest):
    """VMのモックを設定"""
    mock = Mock(spec=vim.VirtualMachine)
    mock.name = "test-vm"
    mock.config = Mock()
    mock.config.instanceUuid = "12345678-1234-5678-1234-567812345678"
    mock.config.uuid = "87654321-8765-4321-8765-432187654321"
    mock.config.hardware = Mock()
    mock.config.hardware.memoryMB = 4096
    mock.config.hardware.numCPU = 2
    mock.config.hardware.device = [mock_disk, mock_network]
    mock.config.template = False
    mock.config.version = "vmx-19"
    mock.guest = mock_guest
    mock.summary = Mock()
    mock.summary.config = Mock()
    mock.summary.config.name = "test-vm"
    mock.summary.config.uuid = "87654321-8765-4321-8765-432187654321"
    mock.summary.config.instanceUuid = "12345678-1234-5678-1234-567812345678"
    mock.summary.config.memorySizeMB = 4096
    mock.summary.config.numCpu = 2
    mock.summary.config.template = False
    mock.summary.config.vmPathName = "[test-datastore] test-vm/test-vm.vmx"
    mock.summary.config.guestFullName = "Red Hat Enterprise Linux 8 (64-bit)"
    mock.summary.config.hwVersion = "vmx-19"
    mock.summary.runtime = Mock()
    mock.summary.runtime.powerState = "poweredOn"
    mock.summary.runtime.host = Mock()
    mock.summary.runtime.host.name = "test-host"
    mock.summary.runtime.host.parent = Mock()
    mock.summary.runtime.host.parent.name = "test-cluster"

    return mock

@pytest.fixture
def mock_folder(mock_vm):
    """フォルダのモックを作成"""
    mock = Mock()
    mock.childEntity = [mock_vm]
    return mock

@pytest.fixture
def setup_inventory_path(mock_content, mock_folder):
    """FindByInventoryPathのセットアップを行う"""
    mock_content.searchIndex.FindByInventoryPath.return_value = mock_folder
    return mock_content

@pytest.fixture
def setup_search_index(mock_content, mock_vm):
    """SearchIndexのセットアップを行う"""
    mock_content.searchIndex.FindByUuid.return_value = mock_vm
    return mock_content

@pytest.fixture(autouse=True)
def mock_connector(monkeypatch):
    """Connectorクラスのモックを作成"""
    mock_service_instance = Mock()
    mock_content = Mock()
    mock_datacenter = Mock()
    mock_datacenter.name = "test-datacenter"
    mock_content.rootFolder = Mock()
    mock_content.rootFolder.childEntity = [mock_datacenter]
    mock_service_instance.RetrieveContent.return_value = mock_content

    def mock_get_service_instances(configs):
        return {"test-vcenter": mock_service_instance}

    def mock_get_vmware_content(vcenter_name):
        return mock_content

    monkeypatch.setattr(Connector, "get_service_instances", mock_get_service_instances)
    monkeypatch.setattr(Connector, "get_vmware_content", mock_get_vmware_content)

@pytest.fixture
def setup_view_manager(mock_vm):
    """ViewManagerのセットアップを行う"""
    mock_content = MockFactory.create_content()
    return MockFactory.create_view_manager(mock_content, [mock_vm])

@pytest.fixture
def setup_empty_view_manager():
    """空のViewManagerのセットアップを行う"""
    mock_content = MockFactory.create_content()
    return MockFactory.create_empty_view_manager(mock_content)

def test_get_vms_by_vm_folders_success(setup_inventory_path):
    """フォルダ指定でVM一覧の取得が成功するケースをテスト"""
    mock_content = setup_inventory_path

    # Vmクラスのクラスメソッドを直接テスト
    result = Vm.get_vms_by_vm_folders(
        content=mock_content,
        vm_folders=["test-folder"]
    )

    # 結果を検証
    assert len(result) == 1
    vm_info = result[0]
    assert vm_info.name == "test-vm"
    assert vm_info.instanceUuid == "12345678-1234-5678-1234-567812345678"
    assert vm_info.uuid == "87654321-8765-4321-8765-432187654321"
    assert vm_info.hwVersion == "vmx-19"
    assert vm_info.memorySizeMB == 4096
    assert vm_info.numCpu == 2
    assert vm_info.powerState == "poweredOn"
    assert vm_info.guestFullName == "Red Hat Enterprise Linux 8 (64-bit)"
    assert vm_info.esxiHostname == "test-host"
    assert vm_info.cluster == "test-cluster"

def test_get_vm_by_instance_uuid_success(setup_search_index):
    """インスタンスUUIDを指定してVMを取得するケースをテスト"""
    mock_content = setup_search_index

    # Vmクラスのクラスメソッドを直接テスト
    result = Vm.get_vm_by_instance_uuid(
        content=mock_content,
        instance_uuid="12345678-1234-5678-1234-567812345678"
    )

    # 結果を検証
    assert result.name == "test-vm"
    assert result.instanceUuid == "12345678-1234-5678-1234-567812345678"
    assert result.uuid == "87654321-8765-4321-8765-432187654321"
    assert result.hwVersion == "vmx-19"
    assert result.memorySizeMB == 4096
    assert result.numCpu == 2
    assert result.powerState == "poweredOn"
    assert result.guestFullName == "Red Hat Enterprise Linux 8 (64-bit)"
    assert result.esxiHostname == "test-host"
    assert result.cluster == "test-cluster"

def test_vm_not_found(setup_search_index):
    """存在しないVMを検索した場合のテスト"""
    mock_content = setup_search_index
    mock_content.searchIndex.FindByUuid.return_value = None

    # HTTPExceptionが発生することを検証
    with pytest.raises(HTTPException) as excinfo:
        Vm.get_vm_by_instance_uuid(
            content=mock_content,
            instance_uuid="not-exist-uuid"
        )

    # 例外のステータスコードとメッセージを検証
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "VM not found"
