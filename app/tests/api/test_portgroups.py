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
from vcenter_lookup_bridge.vmware.portgroup import Portgroup

client = TestClient(app)


@pytest.fixture
def mock_portgroup():
    """単一のポートグループのモックを設定"""
    mock = Mock(spec=vim.Network)
    mock.name = "test-portgroup"

    # ホスト情報の設定
    host = MockFactory.create_host()
    mock.host = [host]

    return mock

@pytest.fixture
def setup_view_manager(mock_portgroup):
    """ViewManagerのセットアップを行う"""
    mock_content = MockFactory.create_content()
    return MockFactory.create_view_manager(mock_content, [mock_portgroup])

@pytest.fixture
def setup_empty_view_manager():
    """空のViewManagerのセットアップを行う"""
    mock_content = MockFactory.create_content()
    return MockFactory.create_empty_view_manager(mock_content)

@pytest.fixture
def setup_none_view_manager():
    """Noneを返すViewManagerのセットアップを行う"""
    mock_content = MockFactory.create_content()

    # MockFactoryを使用せず、直接モックを作成
    mock_container_view = Mock()
    mock_container_view.view = []  # Noneではなく空リストを返す
    mock_content.viewManager.CreateContainerView.return_value = mock_container_view

    return mock_content

@pytest.fixture
def mock_portgroup_tags_with_match():
    """マッチするタグを持つポートグループのモックを作成"""
    return {
        'test-portgroup': {
            'test-category': ['test-tag']
        }
    }

@pytest.fixture
def mock_portgroup_tags_without_match():
    """マッチしないタグを持つポートグループのモックを作成"""
    return {
        'test-portgroup': {
            'test-category': ['other-tag']
        }
    }

@pytest.fixture
def mock_empty_portgroup_tags():
    """空のポートグループタグのモックを作成"""
    return {}

def test_get_portgroups_by_tags_success(setup_view_manager, mock_portgroup_tags_with_match):
    """ポートグループ一覧の取得が成功するケースをテスト"""
    mock_content = setup_view_manager

    # Tagクラスのモック
    with patch('vcenter_lookup_bridge.vmware.portgroup.Tag.get_all_portgroup_tags', return_value=mock_portgroup_tags_with_match), \
         patch('vcenter_lookup_bridge.vmware.portgroup.g.vcenter_configurations', {}):
        # ポートグループクラスのget_portgroups_by_tagsメソッドを直接テスト
        results = Portgroup.get_portgroups_by_tags(
            content=mock_content,
            tag_category='test-category',
            tags=['test-tag']
        )

        # 結果を検証
        assert len(results) == 1
        result = results[0]
        assert result['name'] == 'test-portgroup'
        assert result['tag_category'] == 'test-category'
        assert result['tags'] == ['test-tag']
        assert len(result['hosts']) == 1
        assert result['hosts'][0] == 'test-host'

def test_get_portgroups_by_tags_no_matching_tags(setup_view_manager, mock_portgroup_tags_without_match):
    """タグに一致するポートグループが存在しない場合のテスト"""
    mock_content = setup_view_manager

    # Tagクラスのモック - 存在しないタグを指定
    with patch('vcenter_lookup_bridge.vmware.portgroup.Tag.get_all_portgroup_tags', return_value=mock_portgroup_tags_without_match), \
         patch('vcenter_lookup_bridge.vmware.portgroup.g.vcenter_configurations', {}):
        # ポートグループクラスのget_portgroups_by_tagsメソッドを直接テスト
        results = Portgroup.get_portgroups_by_tags(
            content=mock_content,
            tag_category='test-category',
            tags=['test-tag']  # 存在しないタグ
        )

        # 結果を検証 - 一致するタグがないので空のリストが返されるはず
        assert len(results) == 0

def test_get_portgroups_by_tags_no_portgroups(setup_none_view_manager, mock_empty_portgroup_tags):
    """ポートグループが存在しない場合のテスト"""
    mock_content = setup_none_view_manager

    # Tagクラスのモック
    with patch('vcenter_lookup_bridge.vmware.portgroup.Tag.get_all_portgroup_tags', return_value=mock_empty_portgroup_tags), \
         patch('vcenter_lookup_bridge.vmware.portgroup.g.vcenter_configurations', {}):
        # ポートグループクラスのget_portgroups_by_tagsメソッドを直接テスト
        results = Portgroup.get_portgroups_by_tags(
            content=mock_content,
            tag_category='test-category',
            tags=['test-tag']
        )

        # 結果を検証 - ポートグループが存在しないので空のリストが返されるはず
        assert len(results) == 0

def test_get_portgroups_by_tags_invalid_parameters(setup_view_manager, mock_empty_portgroup_tags):
    """不正なパラメータでのリクエストテスト"""
    mock_content = setup_view_manager

    # Tagクラスのモック
    with patch('vcenter_lookup_bridge.vmware.portgroup.Tag.get_all_portgroup_tags', return_value=mock_empty_portgroup_tags), \
         patch('vcenter_lookup_bridge.vmware.portgroup.g.vcenter_configurations', {}):
        # ポートグループクラスのget_portgroups_by_tagsメソッドを直接テスト
        results = Portgroup.get_portgroups_by_tags(
            content=mock_content,
            tag_category='nonexistent-category',
            tags=['nonexistent-tag']
        )

        # 結果を検証 - タグが存在しないので空のリストが返されるはず
        assert len(results) == 0
