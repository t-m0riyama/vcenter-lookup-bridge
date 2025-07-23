import os
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException
from pyVmomi import vim
from vcenter_lookup_bridge.schemas.vm_snapshot_parameter import VmSnapshotResponseSchema, VmSnapshotListResponseSchema
from vcenter_lookup_bridge.utils.logging import Logging
import urllib.parse


class VmSnapshot(object):
    """スナップショット情報を取得するクラス"""

    # Const
    VLB_MAX_RETRIEVE_VCENTER_OBJECTS_DEFAULT = 1000
    VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT = 4

    @classmethod
    def get_vm_snapshots_from_all_vcenters(
        cls,
        service_instances: dict,
        configs,
        vm_folders: List[str],
        vcenter_name: Optional[str] = None,
        offset=0,
        max_results=100,
        request_id: str = None,
    ) -> list[VmSnapshotResponseSchema]:
        """全vCenterからスナップショット一覧を取得"""

        all_snapshots = []
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
            # vCenterを指定した場合、指定したvCenterから仮想マシン一覧を取得し、各仮想マシンの持つスナップショット情報を取得
            try:
                snapshots = cls._get_vm_snapshots_by_vm_folders_from_vcenter(
                    vcenter_name=vcenter_name,
                    service_instances=service_instances,
                    configs=configs,
                    vm_folders=vm_folders,
                    offset=offset,
                    max_results=max_results,
                )
                Logging.info(f"{request_id} vCenter({vcenter_name})からのスナップショット情報取得に成功")
                all_snapshots.extend(snapshots)
            except Exception as e:
                Logging.error(f"vCenter({vcenter_name})からのスナップショット情報取得に失敗: {e}")
        else:
            # vCenterを指定しない場合、すべてのvCenterから仮想マシン一覧を取得し、各仮想マシンの持つスナップショット情報を取得
            futures = {}
            with ThreadPoolExecutor(max_workers=max_vcenter_web_service_worker_threads) as executor:
                try:
                    # 各vCenterから仮想マシン一覧を取得するスレッドを作成
                    for vcenter_name in configs.keys():
                        futures[vcenter_name] = executor.submit(
                            cls._get_vm_snapshots_by_vm_folders_from_vcenter,
                            vcenter_name,
                            service_instances,
                            configs,
                            vm_folders,
                            offset_vcenter,
                            max_retrieve_vcenter_objects,
                        )

                    # 各スレッドの実行結果を回収
                    for vcenter_name in configs.keys():
                        snapshots = futures[vcenter_name].result()
                        Logging.info(f"{request_id} vCenter({vcenter_name})からのスナップショット情報取得に成功")
                        all_snapshots.extend(snapshots)

                    # オフセットと最大件数の調整
                    all_snapshots = all_snapshots[offset:]
                    if len(all_snapshots) > max_results:
                        all_snapshots = all_snapshots[:max_results]

                except Exception as e:
                    Logging.error(f"{request_id} vCenter({vcenter_name})からのVM取得に失敗: {e}")

        return all_snapshots

    @classmethod
    def _get_vm_snapshots_by_vm_folders_from_vcenter(
        cls,
        vcenter_name: str,
        service_instances: dict,
        configs,
        vm_folders: List[str],
        offset=0,
        max_results=100,
        request_id: str = None,
    ) -> list[VmSnapshotResponseSchema]:
        """特定のvCenterから仮想マシンフォルダを指定して、仮想マシンのスナップショット一覧を取得"""

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
                    snapshot_info = cls._generate_vm_snapshot_info(
                        datacenter=datacenter,
                        vm_folder=vm_folder,
                        vm=vm,
                        vcenter_name=vcenter_name,
                    )
                    results.extend(snapshot_info)
                    vm_count += 1
        return results

    @classmethod
    def get_vm_snapshot_by_instance_uuid_from_all_vcenters(
        cls,
        vcenter_name: str,
        service_instances,
        instance_uuid: str,
        request_id: str = None,
    ) -> list[VmSnapshotResponseSchema]:
        """全vCenterから指定したインスタンスUUIDを持つ仮想マシンのスナップショット情報を取得"""

        all_snapshots = []
        max_vcenter_web_service_worker_threads = int(
            os.getenv(
                "VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS",
                cls.VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT,
            )
        )

        if vcenter_name:
            # vCenterを指定した場合、指定したvCenterから仮想マシン一覧を取得
            try:
                snapshots = cls._get_vm_snapshot_by_instance_uuid(
                    vcenter_name=vcenter_name,
                    service_instances=service_instances,
                    instance_uuid=instance_uuid,
                    request_id=request_id,
                )
                if snapshots is not None:
                    all_snapshots.extend(snapshots)
            except HTTPException as e:
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
                            cls._get_vm_snapshot_by_instance_uuid,
                            vcenter_name,
                            service_instances,
                            instance_uuid,
                            request_id,
                        )

                    # 各スレッドの実行結果を回収
                    for vcenter_name in service_instances.keys():
                        snapshots = futures[vcenter_name].result()
                        if snapshots is not None:
                            all_snapshots.extend(snapshots)
                except HTTPException as e:
                    Logging.info(f"{request_id} vCenter({vcenter_name})からのスナップショット情報取得に失敗: {e}")
                    pass
                except Exception as e:
                    raise e
        return all_snapshots

    @classmethod
    def _get_vm_snapshot_by_instance_uuid(
        cls,
        vcenter_name: str,
        service_instances: dict,
        instance_uuid: str,
        request_id: str = None,
    ) -> list[VmSnapshotResponseSchema]:
        """指定したインスタンスUUIDを持つ仮想マシンのスナップショット情報を取得"""

        # 指定されたvCenterのService Instanceを取得
        if vcenter_name not in service_instances:
            raise HTTPException(status_code=404, detail=f"{request_id} vCenter({vcenter_name}) not found")

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
            return cls._generate_vm_snapshot_info(
                datacenter=datacenter,
                vm_folder=None,
                vm=vm,
                vcenter_name=vcenter_name,
            )
        else:
            return None

    @classmethod
    def _generate_vm_snapshot_info(
        cls, datacenter, vm_folder: Optional[str], vm, vcenter_name: str
    ) -> list[VmSnapshotResponseSchema]:
        """指定した仮想マシンのスナップショット情報を生成"""

        snapshots = []
        vm_snapshots_info = []

        # 仮想マシンのrootスナップショットの有無を確認し、存在する場合は取得
        if hasattr(vm, "snapshot"):
            if hasattr(vm.snapshot, "rootSnapshotList"):
                vm_snapshot_list = vm.snapshot.rootSnapshotList
                # 子スナップショットを再起的に取得
                vm_snapshots = cls._get_snapshots_recursively(vm_snapshot_list)
                if vm_snapshots:
                    if isinstance(vm_snapshots, list):
                        snapshots.extend(vm_snapshots)
                    else:
                        snapshots.append(vm_snapshots)

        for snapshot in snapshots:
            create_time = snapshot.createTime.astimezone().strftime("%Y/%m/%d %H:%M:%S")
            # スナップショットの名前はURLエンコードされている為、デコードする
            snapshot_name = urllib.parse.unquote(snapshot.name)

            # 子スナップショットの有無を確認し、has_childを設定
            if hasattr(snapshot, "childSnapshotList"):
                if len(list(snapshot.childSnapshotList)) > 0:
                    has_child = True
                else:
                    has_child = False
            else:
                has_child = False

            snapshot_info = {
                "vcenter": vcenter_name,
                "datacenter": datacenter.name,
                "vmInstanceUuid": vm.summary.config.instanceUuid,
                "vmName": vm.summary.config.name,
                "vmFolder": vm_folder,
                "name": snapshot_name,
                "id": snapshot.id,
                "parentId": snapshot.parent_id if hasattr(snapshot, "parent_id") else -1,
                "description": snapshot.description,
                "createTime": create_time,
                "hasChild": has_child,
            }
            vm_snapshots_info.append(VmSnapshotResponseSchema(**snapshot_info))
        return vm_snapshots_info

    @staticmethod
    def _get_snapshots_recursively(snapshot_list, parent_id: int = -1):
        snapshots = []
        for snapshot in snapshot_list:
            snapshot.__dict__["parent_id"] = parent_id
            snapshots.append(snapshot)

            # 子スナップショットが存在する場合、取得する
            if hasattr(snapshot, "childSnapshotList"):
                snapshots = snapshots + VmSnapshot._get_snapshots_recursively(snapshot.childSnapshotList, snapshot.id)
        return snapshots
