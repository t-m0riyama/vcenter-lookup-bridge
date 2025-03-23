from typing import Any, Dict, List, Optional
from unittest.mock import Mock


class MockFactory:
    """テスト用のモックオブジェクトを作成するファクトリクラス"""

    @staticmethod
    def create_datacenter(name="test-datacenter") -> Mock:
        """データセンターのモックを作成"""
        mock = Mock()
        mock.name = name
        return mock

    @staticmethod
    def create_content(datacenter=None) -> Mock:
        """コンテンツのモックを作成"""
        if datacenter is None:
            datacenter = MockFactory.create_datacenter()

        mock = Mock()
        mock.rootFolder = Mock()
        mock.rootFolder.childEntity = [datacenter]
        mock.viewManager = Mock()
        mock.searchIndex = Mock()
        return mock

    @staticmethod
    def create_cluster(name="test-cluster") -> Mock:
        """クラスターのモックを作成"""
        mock = Mock()
        mock.name = name
        return mock

    @staticmethod
    def create_host(name="test-host", cluster=None) -> Mock:
        """ホストのモックを作成"""
        if cluster is None:
            cluster = MockFactory.create_cluster()

        mock = Mock()
        mock.name = name
        mock.parent = cluster
        return mock

    @staticmethod
    def create_view_manager(content: Mock, objects: List[Any]) -> Mock:
        """ViewManagerのセットアップを行う"""
        mock_container_view = Mock()
        mock_container_view.view = objects
        content.viewManager.CreateContainerView.return_value = mock_container_view
        return content

    @staticmethod
    def create_empty_view_manager(content: Mock) -> Mock:
        """空のViewManagerのセットアップを行う"""
        return MockFactory.create_view_manager(content, [])

    @staticmethod
    def create_none_view_manager(content: Mock) -> Mock:
        """Noneを返すViewManagerのセットアップを行う"""
        mock_container_view = Mock()
        mock_container_view.view = []
        content.viewManager.CreateContainerView.return_value = mock_container_view
        return content

    @staticmethod
    def create_tags_dict(object_name: str, category_name: str = "test-category", tags: Optional[List[str]] = None) -> Dict:
        """タグ辞書を作成するユーティリティ関数"""
        if tags is None:
            tags = ["test-tag"]

        return {
            object_name: {
                category_name: tags
            }
        }

    @staticmethod
    def create_tags_with_match(object_name: str, category_name: str = "test-category", tags: Optional[List[str]] = None) -> Dict:
        """マッチするタグを作成する"""
        return MockFactory.create_tags_dict(object_name, category_name, tags)

    @staticmethod
    def create_tags_without_match(object_name: str, category_name: str = "test-category", tags: Optional[List[str]] = None) -> Dict:
        """マッチしないタグを作成する"""
        if tags is None:
            tags = ["other-tag"]
        return MockFactory.create_tags_dict(object_name, category_name, tags)

    @staticmethod
    def create_empty_tags() -> Dict:
        """空のタグ辞書を作成"""
        return {}
