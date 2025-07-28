import os
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException
from pyVmomi import vim
from vcenter_lookup_bridge.schemas.vm_folder_parameter import VmFolderResponseSchema
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.vmware.helper import Helper


class VmFolder(object):
    """仮想マシンフォルダ情報を取得するクラス"""

    # Const
    VLB_MAX_RETRIEVE_VCENTER_OBJECTS_DEFAULT = 1000
    VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT = 10

    @classmethod
    @Logging.func_logger
    def get_vm_folders_from_all_vcenters(
        cls,
        service_instances: dict,
        configs,
        vm_folders: List[str] = None,
        vcenter_name: Optional[str] = None,
        offset=0,
        max_results=100,
        request_id: str = None,
    ) -> tuple[list[VmFolderResponseSchema], int]:
        """全vCenterから仮想マシンフォルダ一覧を取得"""

        all_vm_folders = []
        total_vm_folder_count = 0
        max_vcenter_web_service_worker_threads = int(
            os.getenv(
                "VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS",
                cls.VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT,
            )
        )

        if vcenter_name:
            # vCenterを指定した場合、指定したvCenterから仮想マシンフォルダ一覧を取得
            try:
                folders = cls._get_vm_folders_from_vcenter(
                    vcenter_name=vcenter_name,
                    service_instances=service_instances,
                    configs=configs,
                    vm_folders=vm_folders,
                    request_id=request_id,
                )
                Logging.info(f"{request_id} vCenter({vcenter_name})からの仮想マシンフォルダ情報取得に成功")
                all_vm_folders.extend(folders)
                total_vm_folder_count = len(all_vm_folders)
            except Exception as e:
                Logging.error(f"vCenter({vcenter_name})からの仮想マシンフォルダ情報取得に失敗: {e}")
        else:
            # vCenterを指定しない場合、すべてのvCenterから仮想マシンフォルダ一覧を取得
            futures = {}
            with ThreadPoolExecutor(max_workers=max_vcenter_web_service_worker_threads) as executor:
                try:
                    # 各vCenterから仮想マシンフォルダ一覧を取得するスレッドを作成
                    for vcenter_name in configs.keys():
                        futures[vcenter_name] = executor.submit(
                            cls._get_vm_folders_from_vcenter,
                            vcenter_name,
                            service_instances,
                            configs,
                            vm_folders,
                            request_id,
                        )

                    # 各スレッドの実行結果を回収
                    for vcenter_name in configs.keys():
                        folders = futures[vcenter_name].result()
                        Logging.info(f"{request_id} vCenter({vcenter_name})からの仮想マシンフォルダ情報取得に成功")
                        all_vm_folders.extend(folders)

                    # 全仮想マシンフォルダ数を取得
                    total_vm_folder_count = len(all_vm_folders)

                    # オフセットと最大件数の調整
                    all_vm_folders = all_vm_folders[offset:]
                    if len(all_vm_folders) > max_results:
                        all_vm_folders = all_vm_folders[:max_results]

                except Exception as e:
                    Logging.error(f"{request_id} vCenter({vcenter_name})からの仮想マシンフォルダ取得に失敗: {e}")

        return all_vm_folders, total_vm_folder_count

    @classmethod
    @Logging.func_logger
    def _get_vm_folders_from_vcenter(
        cls,
        vcenter_name: str,
        service_instances: dict,
        configs,
        vm_folders: List[str] = None,
        request_id: str = None,
    ) -> list[VmFolderResponseSchema]:
        """特定のvCenterから仮想マシンフォルダ一覧を取得"""

        results = []

        # 指定されたvCenterのService Instanceを取得
        if vcenter_name not in service_instances:
            raise HTTPException(status_code=404, detail=f"vCenter({vcenter_name}) not found")

        content = service_instances[vcenter_name].RetrieveContent()
        config = configs[vcenter_name]

        datacenter = content.rootFolder.childEntity[0]
        base_vm_folder = config["base_vm_folder"]
        search_index = content.searchIndex

        if vm_folders is not None:
            for vm_folder in vm_folders:
                folder = search_index.FindByInventoryPath(f"/{datacenter.name}/vm/{base_vm_folder}/{vm_folder}/")
                if folder is None:
                    Logging.info(
                        f"{request_id} vCenter({vcenter_name})に指定した名前の仮想マシンフォルダ({vm_folder})は見つかりませんでした。"
                    )
                    continue

                vm_folder_info = cls._generate_vm_folder_info(
                    vm_folder=vm_folder,
                    vcenter_name=vcenter_name,
                )
                results.append(vm_folder_info)
        else:
            base_folder = search_index.FindByInventoryPath(f"/{datacenter.name}/vm/{base_vm_folder}/")
            if base_folder is None:
                Logging.info(
                    f"{request_id} vCenter({vcenter_name})に仮想マシンフォルダは見つかりませんでした。{base_vm_folder}フォルダにアクセスできません。"
                )
                # return None
            else:
                for child_folder in base_folder.childEntity:
                    # base_folder直下のサブフォルダのみ取得
                    if isinstance(child_folder, vim.Folder):
                        vm_folder_info = cls._generate_vm_folder_info(
                            vm_folder=child_folder.name,
                            vcenter_name=vcenter_name,
                        )
                        results.append(vm_folder_info)
        return results

    @classmethod
    @Logging.func_logger
    def _generate_vm_folder_info(cls, vm_folder: str, vcenter_name: str) -> VmFolderResponseSchema:
        """仮想マシンフォルダ情報を生成"""

        vm_folder_info = {
            "name": vm_folder,
            "vcenter": vcenter_name,
        }
        return VmFolderResponseSchema(**vm_folder_info)
