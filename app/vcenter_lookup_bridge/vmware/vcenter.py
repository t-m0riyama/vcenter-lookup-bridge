from fastapi import HTTPException
from typing import Optional
from vcenter_lookup_bridge.schemas.vcenter_parameter import VCenterResponseSchema
from vcenter_lookup_bridge.utils.logging import Logging


class VCenter(object):
    """vCenter情報を取得するクラス"""

    # Const
    VLB_MAX_RETRIEVE_VCENTER_OBJECTS_DEFAULT = 1000
    VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT = 10

    @classmethod
    @Logging.func_logger
    def get_all_vcenters(
        cls,
        configs,
        vcenter_name: Optional[str] = None,
        offset=0,
        max_results=100,
        request_id: str = None,
    ) -> list[VCenterResponseSchema]:
        """全vCenter一覧を取得"""

        all_vcenters = []
        if vcenter_name:
            # vCenterを指定した場合、指定したvCenterの情報のみを取得
            # 接続先のvCenterが見つからない場合は空のリストを返す
            if vcenter_name not in configs.keys():
                return all_vcenters

            vcenter_info = cls._generate_vcenter_info(
                config=configs[vcenter_name],
                vcenter_name=vcenter_name,
            )
            Logging.info(f"{request_id} vCenter({vcenter_name})情報取得に成功")
            all_vcenters.append(vcenter_info)
        else:
            for vcenter_name in configs.keys():
                vcenter_info = cls._generate_vcenter_info(
                    config=configs[vcenter_name],
                    vcenter_name=vcenter_name,
                )
                Logging.info(f"{request_id} vCenter({vcenter_name})情報取得に成功")
                all_vcenters.append(vcenter_info)

        return all_vcenters

    @classmethod
    @Logging.func_logger
    def _generate_vcenter_info(cls, config, vcenter_name: str) -> VCenterResponseSchema:
        """vCenter情報を生成"""

        vcenter_info = {
            "name": vcenter_name,
            "hostName": config["hostname"],
            "port": config["port"],
            "description": config["description"],
        }
        return VCenterResponseSchema(**vcenter_info)
