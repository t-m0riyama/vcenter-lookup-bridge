import os

from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException
from pyVmomi import vim
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.vmware.tag import Tag
from vcenter_lookup_bridge.schemas.portgroup_parameter import PortgroupResponseSchema


class Portgroup(object):
    """ポートグループ情報を取得するクラス"""

    # Const
    VLB_MAX_RETRIEVE_VCENTER_OBJECTS_DEFAULT = 1000
    VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT = 10

    @classmethod
    def get_portgroups_by_tags_from_all_vcenters(
        cls,
        service_instances: dict,
        configs,
        tag_category: str,
        tags: list[str],
        vcenter_name: Optional[str] = None,
        offset=0,
        max_results=100,
        requestId: str = None,
    ) -> list[PortgroupResponseSchema]:
        """全vCenterからポートグループ一覧を取得"""

        all_portgroups = []
        offset_vcenter = 0
        max_retrieve_vcenter_objects = int(
            os.getenv(
                "VLB_MAX_RETRIEVE_VCENTER_OBJECTS",
                cls.VLB_MAX_RETRIEVE_VCENTER_OBJECTS_DEFAULT,
            )
        )
        max_vcenter_web_service_worker_threads = int(
            os.getenv(
                "VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS",
                cls.VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT,
            )
        )

        if vcenter_name:
            # vCenterを指定した場合、指定したvCenterからポートグループ一覧を取得
            try:
                portgroups = cls._get_portgroups_by_tags_from_vcenter(
                    vcenter_name=vcenter_name,
                    service_instances=service_instances,
                    configs=configs,
                    tag_category=tag_category,
                    tags=tags,
                    offset=offset,
                    max_results=max_results,
                    requestId=requestId,
                )
                all_portgroups.extend(portgroups)
            except Exception as e:
                Logging.error(f"{requestId} vCenter({vcenter_name})からのポートグループ情報取得に失敗: {e}")
        else:
            # vCenterを指定しない場合、すべてのvCenterからポートグループ一覧を取得
            futures = {}
            with ThreadPoolExecutor(max_workers=max_vcenter_web_service_worker_threads) as executor:
                try:
                    # 各vCenterからポートグループ一覧を取得するスレッドを作成
                    for vcenter_name in configs.keys():
                        futures[vcenter_name] = executor.submit(
                            cls._get_portgroups_by_tags_from_vcenter,
                            vcenter_name,
                            service_instances,
                            configs,
                            tag_category,
                            tags,
                            offset_vcenter,
                            max_retrieve_vcenter_objects,
                            requestId,
                        )

                    # 各スレッドの実行結果を回収
                    for vcenter_name in configs.keys():
                        portgroups = futures[vcenter_name].result()
                        Logging.info(f"{requestId} vCenter({vcenter_name})からのポートグループ情報取得に成功")
                        all_portgroups.extend(portgroups)

                    # オフセットと最大件数の調整
                    all_portgroups = all_portgroups[offset:]
                    if len(all_portgroups) > max_results:
                        all_portgroups = all_portgroups[:max_results]

                except Exception as e:
                    Logging.error(f"{requestId} vCenter({vcenter_name})からのポートグループ情報取得に失敗: {e}")

        return all_portgroups

    @classmethod
    def _get_portgroups_by_tags_from_vcenter(
        cls,
        vcenter_name: str,
        service_instances: dict,
        configs,
        tag_category: str,
        tags: list[str],
        offset: int = 0,
        max_results: int = 100,
        requestId: str = None,
    ) -> list:
        """指定したvCenterからポートグループ一覧を取得"""

        results = []
        portgroup_count = 0

        # 指定されたvCenterのService Instanceを取得
        if vcenter_name not in service_instances:
            raise HTTPException(status_code=404, detail=f"vCenter({vcenter_name}) not found")

        content = service_instances[vcenter_name].RetrieveContent()
        config = configs[vcenter_name]

        cv = content.viewManager.CreateContainerView(container=content.rootFolder, type=[vim.Network], recursive=True)
        portgroups = cv.view
        portgroup_tags = Tag.get_all_portgroup_tags(config=config)

        if portgroups is None:
            return results
        for portgroup in portgroups:
            # offsetまでスキップ
            if portgroup_count < offset:
                portgroup_count += 1
                continue
            # max_resultsまで取得
            if portgroup_count >= offset + max_results:
                break

            if isinstance(portgroup, vim.Network):
                for portgroup_name in portgroup_tags.keys():
                    if portgroup.name == portgroup_name:
                        if tag_category in portgroup_tags[portgroup_name]:
                            portgroup_config = cls._generate_portgroup_info(
                                portgroup=portgroup, vcenter_name=vcenter_name
                            )
                            portgroup_config["tag_category"] = tag_category
                            portgroup_config["tags"] = portgroup_tags[portgroup_name][tag_category]

                            for attached_tag in portgroup_tags[portgroup_name][tag_category]:
                                # すでに結果に追加済みのデータストアであれば、スキップ
                                if portgroup_name in [result["name"] for result in results]:
                                    continue

                                # タグが一致していれば、結果に追加
                                if str(attached_tag) in tags:
                                    results.append(portgroup_config)
                                    portgroup_count += 1
        return results

    @classmethod
    def _generate_portgroup_info(
        cls,
        portgroup,
        vcenter_name: str,
    ):
        """ポートグループ情報を生成"""

        if isinstance(portgroup, vim.Network):
            # ポートグループを利用可能なESXiホストの情報を取得
            hosts = []
            for host in portgroup.host:
                hosts.append(host.name)

            portgroup_config = {
                "name": portgroup.name,
                "vcenter": vcenter_name,
                "hosts": hosts,
            }
            return portgroup_config
