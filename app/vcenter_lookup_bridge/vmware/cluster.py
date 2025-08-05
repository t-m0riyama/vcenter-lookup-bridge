import os
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException
from pyVmomi import vim
from vcenter_lookup_bridge.schemas.cluster_parameter import ClusterResponseSchema
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.vmware.helper import Helper


class Cluster(object):
    """クラスタ情報を取得するクラス"""

    # Const
    VLB_MAX_RETRIEVE_VCENTER_OBJECTS_DEFAULT = 1000
    VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT = 10

    @classmethod
    @Logging.func_logger
    def get_clusters_from_all_vcenters(
        cls,
        service_instances: dict,
        configs,
        cluster_names: List[str] = None,
        vcenter_name: Optional[str] = None,
        offset=0,
        max_results=100,
        request_id: str = None,
    ) -> tuple[list[ClusterResponseSchema], int]:
        """全vCenterからクラスタ一覧を取得"""

        all_clusters = []
        total_cluster_count = 0
        max_vcenter_web_service_worker_threads = int(
            os.getenv(
                "VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS",
                cls.VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT,
            )
        )

        if vcenter_name:
            # vCenterを指定した場合、指定したvCenterからクラスタ一覧を取得
            try:
                clusters = cls._get_clusters_from_vcenter(
                    vcenter_name=vcenter_name,
                    service_instances=service_instances,
                    cluster_names=cluster_names,
                    request_id=request_id,
                )
                Logging.info(f"{request_id} vCenter({vcenter_name})からのクラスタ情報取得に成功")
                all_clusters.extend(clusters)
                total_cluster_count = len(all_clusters)
            except Exception as e:
                Logging.error(f"{request_id} vCenter({vcenter_name})からのクラスタ情報取得に失敗: {e}")
        else:
            # vCenterを指定しない場合、すべてのvCenterからクラスタ一覧を取得
            futures = {}
            with ThreadPoolExecutor(max_workers=max_vcenter_web_service_worker_threads) as executor:
                try:
                    # 各vCenterからクラスタ一覧を取得するスレッドを作成
                    for vcenter_name in configs.keys():
                        futures[vcenter_name] = executor.submit(
                            cls._get_clusters_from_vcenter,
                            vcenter_name,
                            service_instances,
                            cluster_names,
                            request_id,
                        )

                    # 各スレッドの実行結果を回収
                    for vcenter_name in configs.keys():
                        clusters = futures[vcenter_name].result()
                        Logging.info(f"{request_id} vCenter({vcenter_name})からのクラスタ情報取得に成功")
                        all_clusters.extend(clusters)

                    # 全クラスタ数を取得
                    total_cluster_count = len(all_clusters)

                    # オフセットと最大件数の調整
                    all_clusters = all_clusters[offset:]
                    if len(all_clusters) > max_results:
                        all_clusters = all_clusters[:max_results]

                except Exception as e:
                    Logging.error(f"{request_id} vCenter({vcenter_name})からのクラスタ取得に失敗: {e}")

        return all_clusters, total_cluster_count

    @classmethod
    @Logging.func_logger
    def _get_clusters_from_vcenter(
        cls,
        vcenter_name: str,
        service_instances: dict,
        cluster_names: List[str] = None,
        request_id: str = None,
    ) -> list[ClusterResponseSchema]:
        """特定のvCenterからクラスタ一覧を取得"""

        results = []

        # 指定されたvCenterのService Instanceを取得
        if vcenter_name not in service_instances:
            raise HTTPException(status_code=404, detail=f"vCenter({vcenter_name}) not found")

        content = service_instances[vcenter_name].RetrieveContent()
        datacenter = content.rootFolder.childEntity[0]
        clusters = datacenter.hostFolder.childEntity
        for cluster in clusters:
            if isinstance(cluster, vim.ClusterComputeResource):
                # クラスタ名が指定されている場合、指定されたクラスタ名のみ取得
                if cluster_names is not None and cluster.name not in cluster_names:
                    continue

                cluster_info = cls._generate_cluster_info(cluster, vcenter_name)
                results.append(cluster_info)
        return results

    @classmethod
    @Logging.func_logger
    def _generate_cluster_info(cls, cluster: vim.ClusterComputeResource, vcenter_name: str) -> ClusterResponseSchema:
        """クラスタ情報を生成"""

        # クラスタに所属するホストの情報を取得
        hosts = []
        for host in cluster.host:
            hosts.append(host.name)

        cluster_info = {
            "name": cluster.name,
            "status": cluster.overallStatus,
            "hosts": hosts,
            "vcenter": vcenter_name,
        }
        return ClusterResponseSchema(**cluster_info)
