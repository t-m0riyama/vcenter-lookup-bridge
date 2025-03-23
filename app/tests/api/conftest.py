from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from main import app
from vcenter_lookup_bridge.vmware.connector import Connector


@pytest.fixture
def test_client():
    """テストクライアントを作成"""
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
def mock_host(mock_cluster):
    """ホストのモックを作成"""
    mock = Mock()
    mock.name = "test-host"
    mock.parent = mock_cluster
    mock.parent.name = "test-cluster"
    return mock


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
def setup_container_view(mock_content, mock_objects=None):
    """ViewManagerのセットアップを行う共通関数"""
    if mock_objects is None:
        mock_objects = []
    mock_container_view = Mock()
    mock_container_view.view = mock_objects
    mock_content.viewManager.CreateContainerView.return_value = mock_container_view
    return mock_content


@pytest.fixture
def mock_empty_view_manager(mock_content):
    """空のViewManagerのセットアップを行う"""
    return setup_container_view(mock_content, [])


@pytest.fixture
def mock_none_view_manager(mock_content):
    """Noneを返すViewManagerのセットアップを行う"""
    mock_container_view = Mock()
    mock_container_view.view = None
    mock_content.viewManager.CreateContainerView.return_value = mock_container_view
    return mock_content

# タグ関連のユーティリティ関数
def create_tags_dict(object_name, category_name, tags):
    """タグ辞書を作成するユーティリティ関数"""
    return {
        object_name: {
            category_name: tags
        }
    }

@pytest.fixture
def create_tags_with_match():
    """マッチするタグを作成するファクトリフィクスチャ"""
    def _create(object_name, category_name="test-category", tags=None):
        if tags is None:
            tags = ["test-tag"]
        return create_tags_dict(object_name, category_name, tags)
    return _create

@pytest.fixture
def create_tags_without_match():
    """マッチしないタグを作成するファクトリフィクスチャ"""
    def _create(object_name, category_name="test-category", tags=None):
        if tags is None:
            tags = ["other-tag"]
        return create_tags_dict(object_name, category_name, tags)
    return _create
