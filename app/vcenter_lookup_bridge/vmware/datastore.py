import os

from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException
from pyVmomi import vim
from vcenter_lookup_bridge.schemas.datastore_parameter import DatastoreResponseSchema
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.vmware.host_helper import HostHelper
from vcenter_lookup_bridge.vmware.tag import Tag


class Datastore(object):
    """データストア情報を取得するクラス"""

    # Const
    VLB_MAX_RETRIEVE_VCENTER_OBJECTS_DEFAULT = 1000
    VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT = 10

    @classmethod
    @Logging.func_logger
    def get_datastores_by_tags_from_all_vcenters(
        cls,
        service_instances: dict,
        configs,
        tag_category: str,
        tags: list[str],
        vcenter_name: Optional[str] = None,
        offset=0,
        max_results=100,
        request_id: str = None,
    ) -> tuple[list[DatastoreResponseSchema], int]:
        """全vCenterからデータストア一覧を取得"""

        all_datastores = []
        total_datastore_count = 0
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
                datastores = cls._get_datastores_by_tags(
                    vcenter_name=vcenter_name,
                    service_instances=service_instances,
                    configs=configs,
                    tag_category=tag_category,
                    tags=tags,
                    offset=offset,
                    max_results=max_results,
                    request_id=request_id,
                )
                all_datastores.extend(datastores)
                total_datastore_count = len(all_datastores)
            except Exception as e:
                Logging.error(f"{request_id} vCenter({vcenter_name})からのデータストア情報取得に失敗: {e}")
                raise e
        else:
            # vCenterを指定しない場合、すべてのvCenterからデータストア一覧を取得
            futures = {}
            with ThreadPoolExecutor(max_workers=max_vcenter_web_service_worker_threads) as executor:
                try:
                    # 各vCenterからデータストア一覧を取得するスレッドを作成
                    for vcenter_name in configs.keys():
                        futures[vcenter_name] = executor.submit(
                            cls._get_datastores_by_tags,
                            vcenter_name,
                            service_instances,
                            configs,
                            tag_category,
                            tags,
                            offset_vcenter,
                            max_retrieve_vcenter_objects,
                            request_id,
                        )

                    # 各スレッドの実行結果を回収
                    for vcenter_name in configs.keys():
                        datastores = futures[vcenter_name].result()
                        Logging.info(f"{request_id} vCenter({vcenter_name})からのデータストア情報取得に成功")
                        all_datastores.extend(datastores)

                    # 全データストア数を取得
                    total_datastore_count = len(all_datastores)

                    # オフセットと最大件数の調整
                    all_datastores = all_datastores[offset:]
                    if len(all_datastores) > max_results:
                        all_datastores = all_datastores[:max_results]

                except Exception as e:
                    Logging.error(f"{request_id} vCenter({vcenter_name})からのデータストア情報取得に失敗: {e}")

        return all_datastores, total_datastore_count

    @classmethod
    @Logging.func_logger
    def _get_datastores_by_tags(
        cls,
        vcenter_name: str,
        service_instances: dict,
        configs,
        tag_category: str,
        tags: list[str],
        offset: int = 0,
        max_results: int = 100,
        request_id: str = None,
    ) -> list[DatastoreResponseSchema]:
        """指定したvCenterからデータストア一覧を取得"""

        results = []
        datastore_count = 0

        # 指定されたvCenterのService Instanceを取得
        if vcenter_name not in service_instances:
            raise HTTPException(
                status_code=404, detail=f"指定したvCenter({vcenter_name})が接続先に登録されていません。"
            )

        content = service_instances[vcenter_name].RetrieveContent()
        config = configs[vcenter_name]

        cv = content.viewManager.CreateContainerView(container=content.rootFolder, type=[vim.Datastore], recursive=True)
        datastores = cv.view
        datastore_tags = Tag.get_all_datastore_tags(config=config)
        if datastore_tags is None:
            raise HTTPException(status_code=500, detail="データストアのタグを取得中にエラーが発生しました。")

        for datastore in datastores:
            # offsetまでスキップ
            if datastore_count < offset:
                datastore_count += 1
                continue
            # max_resultsまで取得
            if datastore_count >= offset + max_results:
                break

            if isinstance(datastore, vim.Datastore):
                for datastore_name in datastore_tags.keys():
                    if datastore.name == datastore_name:
                        if tag_category in datastore_tags[datastore_name]:
                            datastore_config = cls._generate_datastore_info(
                                datastore=datastore, content=content, vcenter_name=vcenter_name
                            )
                            datastore_config["tag_category"] = tag_category
                            datastore_config["tags"] = datastore_tags[datastore_name][tag_category]

                            for attached_tag in datastore_tags[datastore_name][tag_category]:
                                # すでに結果に追加済みのデータストアであれば、スキップ
                                if datastore_name in [result["name"] for result in results]:
                                    continue

                                # タグが一致していれば、結果に追加
                                if str(attached_tag) in tags:
                                    results.append(datastore_config)
                                    datastore_count += 1
        return results

    @classmethod
    @Logging.func_logger
    def _generate_datastore_info(cls, datastore, content, vcenter_name: str):
        """データストア情報を生成"""

        if isinstance(datastore, vim.Datastore):
            # データストアをマウントしているホストの情報を取得
            hosts = []
            for host in datastore.host:
                hosts.append((HostHelper.get_host_by_object_key(content=content, object_key=host.key))["name"])

            datastore_config = {
                "name": datastore.name,
                "vcenter": vcenter_name,
                "tags": datastore.tag,
                "type": str(datastore.summary.type),
                "capacityGB": int(datastore.summary.capacity / 1024**3),
                "freeSpaceGB": int(datastore.summary.freeSpace / 1024**3),
                "hosts": hosts,
            }
            return datastore_config
