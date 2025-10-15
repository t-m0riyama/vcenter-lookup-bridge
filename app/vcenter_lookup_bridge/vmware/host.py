import os
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException
from pyVmomi import vim
from vcenter_lookup_bridge.schemas.host_parameter import HostResponseSchema, HostDetailResponseSchema
from vcenter_lookup_bridge.utils.logging import Logging


class Host(object):
    """ESXiホスト情報を取得するクラス"""

    # Const
    VLB_MAX_RETRIEVE_VCENTER_OBJECTS_DEFAULT = 1000
    VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT = 10

    @classmethod
    @Logging.func_logger
    def get_hosts_from_all_vcenters(
        cls,
        service_instances: dict,
        configs,
        vcenter_name: Optional[str] = None,
        offset=0,
        max_results=100,
        request_id: str = None,
    ) -> tuple[list[HostResponseSchema], int]:
        """全vCenterからESXiホスト一覧を取得"""

        all_hosts = []
        total_host_count = 0
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
            # vCenterを指定した場合、指定したvCenterからESXiホスト一覧を取得
            try:
                hosts = cls._get_hosts_from_vcenter(
                    vcenter_name=vcenter_name,
                    service_instances=service_instances,
                    configs=configs,
                    offset=offset,
                    max_results=max_results,
                    request_id=request_id,
                )
                all_hosts.extend(hosts)
                total_host_count = len(all_hosts)
            except Exception as e:
                Logging.error(f"{request_id} vCenter({vcenter_name})からのESXiホスト情報取得に失敗: {e}")
                raise e
        else:
            # vCenterを指定しない場合、すべてのvCenterからESXiホスト一覧を取得
            futures = {}
            with ThreadPoolExecutor(max_workers=max_vcenter_web_service_worker_threads) as executor:
                try:
                    # 各vCenterからESXiホスト一覧を取得するスレッドを作成
                    for vcenter_name in configs.keys():
                        futures[vcenter_name] = executor.submit(
                            cls._get_hosts_from_vcenter,
                            vcenter_name,
                            service_instances,
                            configs,
                            offset_vcenter,
                            max_retrieve_vcenter_objects,
                            request_id,
                        )

                    # 各スレッドの実行結果を回収
                    for vcenter_name in configs.keys():
                        hosts = futures[vcenter_name].result()
                        Logging.info(f"{request_id} vCenter({vcenter_name})からのESXiホスト情報取得に成功")
                        all_hosts.extend(hosts)

                    # 全ESXiホスト数を取得
                    total_host_count = len(all_hosts)

                    # オフセットと最大件数の調整
                    all_hosts = all_hosts[offset:]
                    if len(all_hosts) > max_results:
                        all_hosts = all_hosts[:max_results]

                except Exception as e:
                    Logging.error(f"{request_id} vCenter({vcenter_name})からのESXiホスト情報取得に失敗: {e}")

        return all_hosts, total_host_count

    @classmethod
    @Logging.func_logger
    def _get_hosts_from_vcenter(
        cls,
        vcenter_name: str,
        service_instances: dict,
        configs,
        offset=0,
        max_results=100,
        request_id: str = None,
    ) -> list[HostResponseSchema]:
        """特定のvCenterからESXiホスト一覧を取得"""

        results = []

        # 指定されたvCenterのService Instanceを取得
        if vcenter_name not in service_instances:
            raise HTTPException(
                status_code=404, detail=f"指定したvCenter({vcenter_name})が接続先に登録されていません。"
            )

        content = service_instances[vcenter_name].RetrieveContent()
        config = configs[vcenter_name]

        datacenter = content.rootFolder.childEntity[0]
        container = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
        hosts = container.view
        host_count = 0

        for host in hosts:
            if host_count < offset:
                host_count += 1
                continue
            if host_count >= offset + max_results:
                break

            if isinstance(host, vim.HostSystem):
                host_info = cls._generate_host_info(
                    content=content,
                    datacenter=datacenter,
                    host=host,
                    vcenter_name=vcenter_name,
                    is_detail=False,
                )
                results.append(host_info)
                host_count += 1
        return results

    @classmethod
    @Logging.func_logger
    def get_host_by_uuid_from_all_vcenters(
        cls,
        vcenter_name: str,
        service_instances: dict,
        host_uuid: str,
        request_id: str = None,
    ) -> HostResponseSchema:
        """指定したUUIDのESXiホストを取得"""

        result = None
        max_vcenter_web_service_worker_threads = int(
            os.getenv(
                "VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS",
                cls.VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT,
            )
        )

        if vcenter_name:
            # vCenterを指定した場合、指定したvCenterからESXiホストを取得
            try:
                host = cls._get_host_by_uuid(
                    vcenter_name=vcenter_name,
                    service_instances=service_instances,
                    host_uuid=host_uuid,
                    request_id=request_id,
                )
                if host is not None:
                    Logging.info(f"{request_id} vCenter({vcenter_name})からのESXiホスト情報取得に成功")
                    result = host
            except HTTPException as e:
                Logging.info(f"{request_id} vCenter({vcenter_name})からのESXiホスト情報取得に失敗: {e}")
                pass
            except Exception as e:
                raise e
        else:
            # vCenterを指定しない場合、すべてのvCenterからESXiホストを取得
            futures = {}
            with ThreadPoolExecutor(max_workers=max_vcenter_web_service_worker_threads) as executor:
                try:
                    # 各vCenterからESXiホストを取得するスレッドを作成
                    for vcenter_name in service_instances.keys():
                        futures[vcenter_name] = executor.submit(
                            cls._get_host_by_uuid,
                            vcenter_name,
                            service_instances,
                            host_uuid,
                            request_id,
                        )

                    # 各スレッドの実行結果を回収
                    for vcenter_name in service_instances.keys():
                        host = futures[vcenter_name].result()
                        if host is not None:
                            Logging.info(f"{request_id} vCenter({vcenter_name})からのESXiホスト情報取得に成功")
                            result = host
                        else:
                            Logging.info(
                                f"{request_id} vCenter({vcenter_name})にUUID({host_uuid})を持つESXiホストは見つかりませんでした。"
                            )
                except HTTPException as e:
                    Logging.info(f"{request_id} vCenter({vcenter_name})からのESXiホスト情報取得に失敗: {e}")
                    pass
                except Exception as e:
                    raise e
        return result

    @classmethod
    @Logging.func_logger
    def _get_host_by_uuid(
        cls,
        vcenter_name: str,
        service_instances: dict,
        host_uuid: str,
        request_id: str = None,
    ) -> HostResponseSchema:
        """UUIDとvCenterを指定して、ESXiホスト情報を取得"""

        # 指定されたvCenterのService Instanceを取得
        if vcenter_name not in service_instances:
            raise HTTPException(
                status_code=404, detail=f"指定したvCenter({vcenter_name})が接続先に登録されていません。"
            )

        content = service_instances[vcenter_name].RetrieveContent()
        datacenter = content.rootFolder.childEntity[0]
        search_index = content.searchIndex

        # ESXiホストをUUIDを指定して検索
        host = search_index.FindByUuid(
            uuid=host_uuid,
            vmSearch=False,
            instanceUuid=False,
        )

        if isinstance(host, vim.HostSystem):
            return cls._generate_host_info(
                content=content,
                datacenter=datacenter,
                host=host,
                vcenter_name=vcenter_name,
                is_detail=True,
            )
        else:
            Logging.info(
                f"{request_id} vCenter({vcenter_name})にUUID({host_uuid})を持つESXiホストは見つかりませんでした。"
            )
            return None

    @classmethod
    @Logging.func_logger
    def _count_all_hosts(cls, content) -> int:
        root_folder = content.rootFolder
        view_hosts = content.viewManager.CreateContainerView(
            container=root_folder, type=[vim.HostSystem], recursive=True
        )
        return len(view_hosts.view)

    @classmethod
    @Logging.func_logger
    def _generate_host_info(
        cls, content, datacenter, host, vcenter_name: str = None, is_detail: bool = False
    ) -> HostResponseSchema | HostDetailResponseSchema:
        """ESXiホスト情報を生成"""

        if is_detail:
            if hasattr(host, "config"):
                # シミュレーター以外のESXiホストの場合、IPアドレスを追加
                ip_address = host.config.network.vnic[0].spec.ip.ipAddress if host.config.network.vnic else None
            else:
                # シミュレーターのESXiホストの場合、ダミーのIPアドレスを追加
                ip_address = "127.0.0.1"

        if hasattr(host, "runtime"):
            # シミュレーター以外のESXiホストの場合、電源状態を追加
            power_state = host.runtime.powerState
        else:
            # シミュレーターのESXiホストの場合、ダミーの電源状態を追加
            power_state = "poweredOn"

        if hasattr(host, "summary"):
            # シミュレーター以外のESXiホストの場合、各種ハードウェア情報などを追加
            uuid = host.summary.hardware.uuid
            esxi_version = host.summary.config.product.version
            num_cpu_sockets = host.summary.hardware.numCpuPkgs
            num_cpu_cores = host.summary.hardware.numCpuCores
            num_cpu_threads = host.summary.hardware.numCpuThreads
            memory_size_mb = int(host.summary.hardware.memorySize / 1024 / 1024)
            if is_detail:
                esxi_version_full = host.summary.config.product.fullName
                hardware_vendor = host.summary.hardware.vendor
                hardware_model = host.summary.hardware.model
                cpu_model = host.summary.hardware.cpuModel
        else:
            # シミュレーターのESXiホストの場合、ダミーの各種ハードウェア情報などを追加
            uuid = "99999999-1234-1234-1234-999999999999"
            esxi_version = "8.0.3"
            num_cpu_sockets = 1
            num_cpu_cores = 32
            num_cpu_threads = 64
            memory_size_mb = 65536
            if is_detail:
                esxi_version_full = "VMware ESXi 8.0.3 build-12345"
                hardware_vendor = "Dummy Vendor"
                hardware_model = "Dummy Model 000"
                cpu_model = "Dummy CPU Model 000"

        if is_detail:
            # データストア一覧の取得
            datastores = []
            for ds in host.datastore:
                datastores.append(
                    {
                        "name": ds.name,
                        "status": ds.overallStatus,
                        "type": ds.summary.type,
                        "capacityGB": int(ds.summary.capacity / 1024 / 1024 / 1024),
                        "freeSpaceGB": int(ds.summary.freeSpace / 1024 / 1024 / 1024),
                    }
                )

            # ポートグループ一覧の取得
            portgroups = []
            for net in host.network:
                portgroups.append({"name": net.name})

            # vSwitch一覧の取得
            vswitches = []
            if hasattr(host, "config"):
                if hasattr(host.config, "network"):
                    # 標準スイッチ一覧を取得
                    for vss in host.config.network.vswitch:
                        vswitches.append({"name": vss.name})

                    # 分散スイッチ一覧を取得
                    dvs_view = content.viewManager.CreateContainerView(
                        content.rootFolder, [vim.DistributedVirtualSwitch], True
                    )
                    for dvs in dvs_view.view:
                        vswitches.append({"name": dvs.name})

        if is_detail:
            host_info = {
                "vcenter": vcenter_name,
                "datacenter": datacenter.name,
                "cluster": host.parent.name,
                "name": host.name,
                "uuid": uuid,
                "status": host.overallStatus,
                "powerState": power_state,
                "ipAddress": ip_address,
                "esxiVersion": esxi_version,
                "esxiVersionFull": esxi_version_full,
                "hardwareVendor": hardware_vendor,
                "hardwareModel": hardware_model,
                "numCpuSockets": num_cpu_sockets,
                "numCpuCores": num_cpu_cores,
                "numCpuThreads": num_cpu_threads,
                "cpuModel": cpu_model,
                "memorySizeMB": memory_size_mb,
                "datastores": datastores,
                "portgroups": portgroups,
                "vswitches": vswitches,
            }
            return HostDetailResponseSchema(**host_info)
        else:
            host_info = {
                "vcenter": vcenter_name,
                "datacenter": datacenter.name,
                "name": host.name,
                "uuid": uuid,
                "status": host.overallStatus,
                "esxiVersion": esxi_version,
                "numCpuSockets": num_cpu_sockets,
                "numCpuCores": num_cpu_cores,
                "numCpuThreads": num_cpu_threads,
                "memorySizeMB": memory_size_mb,
            }
            return HostResponseSchema(**host_info)
