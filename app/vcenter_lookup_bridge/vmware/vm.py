from typing import List, Optional

from fastapi import HTTPException
from pyVmomi import vim
from vcenter_lookup_bridge.schemas.vm_parameter import VmResponseSchema
from vcenter_lookup_bridge.utils.logging import Logging


class Vm(object):

    @classmethod
    def get_vms_by_vm_folders(cls, content, vm_folders: List[str], offset=0, max_results=100) -> list[VmResponseSchema]:
        results = []
        datacenter = content.rootFolder.childEntity[0]
        search_index = content.searchIndex
        vm_count = 0

        for vm_folder in vm_folders:
            folder = search_index.FindByInventoryPath(f"/{datacenter.name}/vm/{vm_folder}/")
            if folder is None:
                Logging.warning(f"仮想マシンフォルダ({vm_folder})が見つかりませんでした。")
                continue

            # max_resultsまで取得
            if vm_count >= offset + max_results:
                break

            for vm in folder.childEntity:
                # offsetまでスキップ
                if vm_count < offset:
                    vm_count += 1
                    continue
                # max_resultsまで取得
                if vm_count >= offset + max_results:
                    break

                if isinstance(vm, vim.VirtualMachine):
                    vm_config = cls._generate_vm_info(datacenter, vm_folder, vm)
                    results.append(vm_config)
                    vm_count += 1
        return results

    @classmethod
    def get_vm_by_instance_uuid(cls, content, instance_uuid: str) -> VmResponseSchema:
        datacenter = content.rootFolder.childEntity[0]
        search_index = content.searchIndex

        # 仮想マシンをインスタンスUUID
        vm = search_index.FindByUuid(
            uuid=instance_uuid,
            vmSearch=True,
            instanceUuid=True,
        )

        if not isinstance(vm, vim.VirtualMachine):
            raise HTTPException(status_code=404, detail="VM not found")

        return cls._generate_vm_info(datacenter=datacenter, vm_folder=None, vm=vm)

    @classmethod
    def _generate_vm_info(cls, datacenter, vm_folder: Optional[str], vm) -> VmResponseSchema:
        disk_devices = []
        network_devices = []
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualDisk):
                disk_devices.append(
                    {
                        "label": device.deviceInfo.label,
                        "datastore": device.backing.datastore.name,
                        "sizeGB": int(device.capacityInKB / 1024 ** 2),
                    }
                )
            elif isinstance(device, vim.vm.device.VirtualVmxnet3):
                network_devices.append(
                    {
                        "label": device.deviceInfo.label,
                        "macAddress": device.macAddress,
                        "portgroup": device.backing.deviceName,
                        "connected": device.connectable.connected,
                        "startConnected": device.connectable.startConnected,
                    }
                )

        vm_info = {
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
