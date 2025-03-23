import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from pyVmomi import vim

# アプリケーションのルートディレクトリをPythonパスに追加
app_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, app_root)

from main import app
from tests.api.test_helpers import MockFactory
from vcenter_lookup_bridge.vmware.datastore import Datastore

client = TestClient(app)


@pytest.fixture
def mock_datastore():
    """単一のデータストアのモックを設定"""
    mock = Mock(spec=vim.Datastore)
    mock.name = "test-datastore"
    mock.tag = []

    # サマリー情報の設定
    mock.summary = Mock()
    mock.summary.type = "VMFS"
    mock.summary.capacity = 100 * 1024 * 1024 * 1024  # 100GBをバイト単位で
    mock.summary.freeSpace = 50 * 1024 * 1024 * 1024  # 50GBをバイト単位で
    mock.summary.accessible = True

    # ホスト情報の設定
    host = MockFactory.create_host()
    host_mount = Mock()
    host_mount.key = host
    mock.host = [host_mount]

    return mock

@pytest.fixture
def setup_view_manager(mock_datastore):
    """ViewManagerのセットアップを行う"""
    mock_content = MockFactory.create_content()
    return MockFactory.create_view_manager(mock_content, [mock_datastore])

@pytest.fixture
def setup_empty_view_manager():
    """空のViewManagerのセットアップを行う"""
    mock_content = MockFactory.create_content()
    return MockFactory.create_empty_view_manager(mock_content)

@pytest.fixture
def setup_none_view_manager():
    """空のリストを返すViewManagerのセットアップを行う"""
    mock_content = MockFactory.create_content()

    # 空のリストを返すようにモックを設定
    mock_container_view = Mock()
    mock_container_view.view = []
    mock_content.viewManager.CreateContainerView.return_value = mock_container_view
    return mock_content

@pytest.fixture
def mock_datastore_tags_with_match():
    """マッチするタグを持つデータストアのモックを作成"""
    return {
        'test-datastore': {
            'test-category': ['test-tag']
        }
    }

@pytest.fixture
def mock_datastore_tags_without_match():
    """マッチしないタグを持つデータストアのモックを作成"""
    return {
        'test-datastore': {
            'test-category': ['other-tag']
        }
    }

@pytest.fixture
def mock_empty_datastore_tags():
    """空のデータストアタグのモックを作成"""
    return {}

def test_get_datastores_by_tags_success(setup_view_manager, mock_datastore_tags_with_match):
    """データストア一覧の取得が成功するケースをテスト"""
    mock_content = setup_view_manager

    # Hostクラスのモック
    with patch('vcenter_lookup_bridge.vmware.host.Host.get_host_by_object_key') as mock_get_host:
        mock_get_host.return_value = {'name': 'test-host'}

        # Tagクラスのモック
        with patch('vcenter_lookup_bridge.vmware.datastore.Tag.get_all_datastore_tags', return_value=mock_datastore_tags_with_match), \
             patch('vcenter_lookup_bridge.vmware.datastore.g.vcenter_configurations', {}):
            # データストアクラスのget_datastores_by_tagsメソッドを直接テスト
            results = Datastore.get_datastores_by_tags(
                content=mock_content,
                tag_category='test-category',
                tags=['test-tag'],
                offset=0,
                max_results=100
            )

            # 結果を検証
            assert len(results) == 1
            result = results[0]
            assert result['name'] == 'test-datastore'
            assert result['type'] == 'VMFS'
            assert result['capacityGB'] == 100
            assert result['freeSpaceGB'] == 50
            assert result['tag_category'] == 'test-category'
            assert result['tags'] == ['test-tag']
            assert len(result['hosts']) == 1
            assert result['hosts'][0] == 'test-host'


def test_get_datastores_by_tags_no_matching_tags(setup_view_manager, mock_datastore_tags_without_match):
    """タグに一致するデータストアが存在しない場合のテスト"""
    mock_content = setup_view_manager

    # Hostクラスのモック
    with patch('vcenter_lookup_bridge.vmware.host.Host.get_host_by_object_key') as mock_get_host:
        mock_get_host.return_value = {'name': 'test-host'}

        # Tagクラスのモック - 存在しないタグを指定
        with patch('vcenter_lookup_bridge.vmware.datastore.Tag.get_all_datastore_tags', return_value=mock_datastore_tags_without_match), \
             patch('vcenter_lookup_bridge.vmware.datastore.g.vcenter_configurations', {}):
            # データストアクラスのget_datastores_by_tagsメソッドを直接テスト
            results = Datastore.get_datastores_by_tags(
                content=mock_content,
                tag_category='test-category',
                tags=['test-tag'],  # 存在しないタグ
                offset=0,
                max_results=100
            )

            # 結果を検証 - 一致するタグがないので空のリストが返されるはず
            assert len(results) == 0


def test_get_datastores_by_tags_no_datastores(setup_none_view_manager, mock_empty_datastore_tags):
    """データストアが存在しない場合のテスト"""
    mock_content = setup_none_view_manager

    # Tagクラスのモック
    with patch('vcenter_lookup_bridge.vmware.datastore.Tag.get_all_datastore_tags', return_value=mock_empty_datastore_tags), \
         patch('vcenter_lookup_bridge.vmware.datastore.g.vcenter_configurations', {}):
        # データストアクラスのget_datastores_by_tagsメソッドを直接テスト
        results = Datastore.get_datastores_by_tags(
            content=mock_content,
            tag_category='test-category',
            tags=['test-tag'],
            offset=0,
            max_results=100
        )

        # 結果を検証 - データストアが存在しないので空のリストが返されるはず
        assert len(results) == 0

def test_get_datastores_by_tags_invalid_parameters(setup_view_manager, mock_empty_datastore_tags):
    """不正なパラメータでのリクエストテスト"""
    mock_content = setup_view_manager

    # Tagクラスのモック
    with patch('vcenter_lookup_bridge.vmware.datastore.Tag.get_all_datastore_tags', return_value=mock_empty_datastore_tags), \
         patch('vcenter_lookup_bridge.vmware.datastore.g.vcenter_configurations', {}):
        # データストアクラスのget_datastores_by_tagsメソッドを直接テスト
        results = Datastore.get_datastores_by_tags(
            content=mock_content,
            tag_category='nonexistent-category',
            tags=['nonexistent-tag'],
            offset=0,
            max_results=100
        )

        # 結果を検証 - タグが存在しないので空のリストが返されるはず
        assert len(results) == 0

# このファイルを直接実行した場合にテストを実行
if __name__ == "__main__":
    # カレントディレクトリをappディレクトリに設定しておく
    script_dir = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(script_dir))

    # このファイル内のテストを実行
    pytest.main(["-v", __file__])
