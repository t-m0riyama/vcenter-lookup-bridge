import os
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException
from pyVmomi import vim
from vcenter_lookup_bridge.schemas.vm_parameter import VmResponseSchema
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.vmware.helper import Helper


class Vm(object):
    """仮想マシン情報を取得するクラス"""

    # Const
    VLB_MAX_RETRIEVE_VCENTER_OBJECTS_DEFAULT = 1000
    VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT = 10

    @classmethod
    @Logging.func_logger
    def get_vms_from_all_vcenters(
        cls,
        service_instances: dict,
        configs,
        vm_folders: List[str],
        vcenter_name: Optional[str] = None,
        offset=0,
        max_results=100,
        request_id: str = None,
    ) -> list[VmResponseSchema]:
        """全vCenterから仮想マシン一覧を取得"""

        all_vms = []
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
            # vCenterを指定した場合、指定したvCenterから仮想マシン一覧を取得
            try:
                vms = cls._get_vms_by_vm_folders_from_vcenter(
                    vcenter_name=vcenter_name,
                    service_instances=service_instances,
                    configs=configs,
                    vm_folders=vm_folders,
                    offset=offset,
                    max_results=max_results,
                    request_id=request_id,
                )
                all_vms.extend(vms)
            except Exception as e:
                Logging.error(f"vCenter({vcenter_name})からの仮想マシン情報取得に失敗: {e}")
        else:
            # vCenterを指定しない場合、すべてのvCenterから仮想マシン一覧を取得
            futures = {}
            with ThreadPoolExecutor(max_workers=max_vcenter_web_service_worker_threads) as executor:
                try:
                    # 各vCenterから仮想マシン一覧を取得するスレッドを作成
                    for vcenter_name in configs.keys():
                        futures[vcenter_name] = executor.submit(
                            cls._get_vms_by_vm_folders_from_vcenter,
                            vcenter_name,
                            service_instances,
                            configs,
                            vm_folders,
                            offset_vcenter,
                            max_retrieve_vcenter_objects,
                            request_id,
                        )

                    # 各スレッドの実行結果を回収
                    for vcenter_name in configs.keys():
                        vms = futures[vcenter_name].result()
                        Logging.info(f"{request_id} vCenter({vcenter_name})からの仮想マシン情報取得に成功")
                        all_vms.extend(vms)

                    # オフセットと最大件数の調整
                    all_vms = all_vms[offset:]
                    if len(all_vms) > max_results:
                        all_vms = all_vms[:max_results]

                except Exception as e:
                    Logging.error(f"{request_id} vCenter({vcenter_name})からのVM取得に失敗: {e}")

        return all_vms

    @classmethod
    @Logging.func_logger
    def _get_vms_by_vm_folders_from_vcenter(
        cls,
        vcenter_name: str,
        service_instances: dict,
        configs,
        vm_folders: List[str],
        offset=0,
        max_results=100,
        request_id: str = None,
    ) -> list[VmResponseSchema]:
        """特定のvCenterから仮想マシン一覧を取得"""

        results = []

        # 指定されたvCenterのService Instanceを取得
        if vcenter_name not in service_instances:
            raise HTTPException(status_code=404, detail=f"vCenter({vcenter_name}) not found")

        content = service_instances[vcenter_name].RetrieveContent()
        config = configs[vcenter_name]

        datacenter = content.rootFolder.childEntity[0]
        base_vm_folder = config["base_vm_folder"]
        search_index = content.searchIndex
        vm_count = 0

        for vm_folder in vm_folders:
            folder = search_index.FindByInventoryPath(f"/{datacenter.name}/vm/{base_vm_folder}/{vm_folder}/")
            if folder is None:
                Logging.info(
                    f"{request_id} vCenter({vcenter_name})に仮想マシンフォルダ({vm_folder})は見つかりませんでした。"
                )
                continue

            if vm_count >= offset + max_results:
                break

            for vm in folder.childEntity:
                if vm_count < offset:
                    vm_count += 1
                    continue
                if vm_count >= offset + max_results:
                    break

                if isinstance(vm, vim.VirtualMachine):
                    vm_info = cls._generate_vm_info(
                        content=content,
                        datacenter=datacenter,
                        vm_folder=vm_folder,
                        vm=vm,
                        vcenter_name=vcenter_name,
                    )
                    results.append(vm_info)
                    vm_count += 1
        return results

    @classmethod
    @Logging.func_logger
    def get_vm_by_instance_uuid_from_all_vcenters(
        cls,
        vcenter_name: str,
        service_instances: dict,
        instance_uuid: str,
        request_id: str = None,
    ) -> list[VmResponseSchema]:
        """全vCenterから仮想マシン一覧を取得"""

        all_vms = []
        max_vcenter_web_service_worker_threads = int(
            os.getenv(
                "VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS",
                cls.VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT,
            )
        )

        if vcenter_name:
            # vCenterを指定した場合、指定したvCenterから仮想マシン一覧を取得
            try:
                vms = cls._get_vm_by_instance_uuid(
                    vcenter_name=vcenter_name,
                    service_instances=service_instances,
                    instance_uuid=instance_uuid,
                    request_id=request_id,
                )
                if vms is not None:
                    Logging.info(f"{request_id} vCenter({vcenter_name})からの仮想マシン情報取得に成功")
                    all_vms.append(vms)
            except HTTPException as e:
                Logging.info(f"{request_id} vCenter({vcenter_name})からのVM取得に失敗: {e}")
                pass
            except Exception as e:
                raise e
        else:
            # vCenterを指定しない場合、すべてのvCenterから仮想マシン一覧を取得
            futures = {}
            with ThreadPoolExecutor(max_workers=max_vcenter_web_service_worker_threads) as executor:
                try:
                    # 各vCenterから仮想マシン一覧を取得するスレッドを作成
                    for vcenter_name in service_instances.keys():
                        futures[vcenter_name] = executor.submit(
                            cls._get_vm_by_instance_uuid,
                            vcenter_name,
                            service_instances,
                            instance_uuid,
                            request_id,
                        )

                    # 各スレッドの実行結果を回収
                    for vcenter_name in service_instances.keys():
                        vms = futures[vcenter_name].result()
                        if vms is not None:
                            Logging.info(f"{request_id} vCenter({vcenter_name})からの仮想マシン情報取得に成功")
                            all_vms.append(vms)
                        else:
                            Logging.info(
                                f"{request_id} vCenter({vcenter_name})にインスタンスUUID({instance_uuid})を持つ仮想マシンは見つかりませんでした。"
                            )
                except HTTPException as e:
                    Logging.info(f"{request_id} vCenter({vcenter_name})からのVM取得に失敗: {e}")
                    pass
                except Exception as e:
                    raise e
        return all_vms

    @classmethod
    @Logging.func_logger
    def _get_vm_by_instance_uuid(
        cls,
        vcenter_name: str,
        service_instances: dict,
        instance_uuid: str,
        request_id: str = None,
    ) -> VmResponseSchema:
        """インスタンスUUIDとvCenterを指定して、仮想マシン情報を取得"""

        # 指定されたvCenterのService Instanceを取得
        if vcenter_name not in service_instances:
            raise HTTPException(status_code=404, detail=f"vCenter({vcenter_name}) not found")

        content = service_instances[vcenter_name].RetrieveContent()
        datacenter = content.rootFolder.childEntity[0]
        search_index = content.searchIndex

        # 仮想マシンをインスタンスUUIDを指定して検索
        vm = search_index.FindByUuid(
            uuid=instance_uuid,
            vmSearch=True,
            instanceUuid=True,
        )

        if isinstance(vm, vim.VirtualMachine):
            return cls._generate_vm_info(
                content=content,
                datacenter=datacenter,
                vm_folder=None,
                vm=vm,
                vcenter_name=vcenter_name,
            )
        else:
            Logging.info(
                f"{request_id} vCenter({vcenter_name})にインスタンスUUID({instance_uuid})を持つ仮想マシンは見つかりませんでした。"
            )
            return None

    @classmethod
    @Logging.func_logger
    def _count_all_vms(cls, content) -> int:
        root_folder = content.rootFolder
        view_vms = content.viewManager.CreateContainerView(
            container=root_folder, type=[vim.VirtualMachine], recursive=True
        )
        return len(view_vms.view)

    @classmethod
    @Logging.func_logger
    def _generate_vm_info(
        cls, content, datacenter, vm_folder: Optional[str], vm, vcenter_name: str = None
    ) -> VmResponseSchema:
        """仮想マシン情報を生成"""

        disk_devices = []
        network_devices = []

        if hasattr(vm, "config"):
            # シミュレーター以外の仮想マシンの場合、仮想ディスクとポートグループを追加
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualDisk):
                    disk_devices.append(
                        {
                            "label": device.deviceInfo.label,
                            "datastore": device.backing.datastore.name,
                            "sizeGB": int(device.capacityInKB / 1024**2),
                        }
                    )
                elif isinstance(device, vim.vm.device.VirtualVmxnet3):
                    if isinstance(
                        device.backing,
                        vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo,
                    ):
                        portgroup_name = Helper.get_object_by_object_key(
                            content=content,
                            vimtype=vim.dvs.DistributedVirtualPortgroup,
                            object_key=device.backing.port.portgroupKey,
                        )
                    else:
                        portgroup_name = device.backing.deviceName

                    network_devices.append(
                        {
                            "label": device.deviceInfo.label,
                            "macAddress": device.macAddress,
                            "portgroup": portgroup_name,
                            "connected": device.connectable.connected,
                            "startConnected": device.connectable.startConnected,
                        }
                    )
        else:
            # VCSIMシミュレータの仮想マシンの場合、仮想ディスクとポートグループにダミーデータを追加
            disk_devices.append(
                {
                    "label": "VCSIM Simulator Label",
                    "datastore": "VCSIM Simulator Datastore",
                    "sizeGB": 100,
                }
            )
            portgroup_name = "VCSIM Simulator PortGroup"
            network_devices.append(
                {
                    "label": "VCSIM Simulator Label",
                    "macAddress": "00:11:22:33:44:55",
                    "portgroup": portgroup_name,
                    "connected": True,
                    "startConnected": True,
                }
            )

        vm_info = {
            "vcenter": vcenter_name,
            "datacenter": datacenter.name,
            "cluster": vm.summary.runtime.host.parent.name,
            "esxiHostname": vm.summary.runtime.host.name,
            "hostname": vm.guest.hostName,
            "ipAddress": vm.guest.ipAddress,
            "vmFolder": vm_folder,
            "powerState": vm.summary.runtime.powerState,
            "diskDevices": disk_devices,
            "networkDevices": network_devices,
            "uuid": vm.summary.config.uuid,
            "instanceUuid": vm.summary.config.instanceUuid,
            "name": vm.summary.config.name,
            "numCpu": vm.summary.config.numCpu,
            "memorySizeMB": vm.summary.config.memorySizeMB,
            "template": vm.summary.config.template,
            "vmPathName": vm.summary.config.vmPathName,
            "guestFullName": vm.summary.config.guestFullName,
            "hwVersion": vm.summary.config.hwVersion,
        }
        return VmResponseSchema(**vm_info)
