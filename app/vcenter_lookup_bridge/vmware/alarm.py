import datetime
import os
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException
from pyVmomi import vim
from vcenter_lookup_bridge.schemas.alarm_parameter import AlarmResponseSchema
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.vmware.helper import Helper


class Alarm(object):
    """トリガー済みのアラーム情報を取得するクラス"""

    # Const
    VLB_MAX_RETRIEVE_VCENTER_OBJECTS_DEFAULT = 1000
    VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT = 10
    VLB_MAX_RETRIEVE_ALARMS_PER_VCENTER_DEFAULT = 2000

    @classmethod
    @Logging.func_logger
    def get_alarms_from_all_vcenters(
        cls,
        service_instances: dict,
        configs,
        vcenter_name: Optional[str] = None,
        begin_time: str = None,
        end_time: str = None,
        days_ago_begin: int = None,
        days_ago_end: int = None,
        hours_ago_begin: int = None,
        hours_ago_end: int = None,
        statuses: List[str] = None,
        alarm_sources: List[str] = None,
        acknowledged: bool = None,
        offset=0,
        max_results=100,
        request_id: str = None,
    ) -> tuple[list[AlarmResponseSchema], int]:
        """全vCenterからトリガー済みのアラーム一覧を取得"""

        all_alarms = []
        total_alarm_count = 0
        max_vcenter_web_service_worker_threads = int(
            os.getenv(
                "VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS",
                cls.VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT,
            )
        )

        if vcenter_name:
            # vCenterを指定した場合、指定したvCenterからトリガー済みのアラーム一覧を取得
            try:
                alarms = cls._get_alarms_from_vcenter(
                    vcenter_name=vcenter_name,
                    service_instances=service_instances,
                    begin_time=begin_time,
                    end_time=end_time,
                    days_ago_begin=days_ago_begin,
                    days_ago_end=days_ago_end,
                    hours_ago_begin=hours_ago_begin,
                    hours_ago_end=hours_ago_end,
                    statuses=statuses,
                    alarm_sources=alarm_sources,
                    acknowledged=acknowledged,
                    request_id=request_id,
                )
                Logging.info(f"{request_id} vCenter({vcenter_name})からのトリガー済みアラーム情報取得に成功")
                all_alarms.extend(alarms)
                total_alarm_count = len(all_alarms)
            except Exception as e:
                Logging.error(f"{request_id} vCenter({vcenter_name})からのトリガー済みアラーム情報取得に失敗: {e}")
        else:
            # vCenterを指定しない場合、すべてのvCenterからトリガー済みのアラーム一覧を取得
            futures = {}
            with ThreadPoolExecutor(max_workers=max_vcenter_web_service_worker_threads) as executor:
                try:
                    # 各vCenterからトリガー済みのアラーム一覧を取得するスレッドを作成
                    for vcenter_name in configs.keys():
                        futures[vcenter_name] = executor.submit(
                            cls._get_alarms_from_vcenter,
                            vcenter_name,
                            service_instances,
                            begin_time,
                            end_time,
                            days_ago_begin,
                            days_ago_end,
                            hours_ago_begin,
                            hours_ago_end,
                            statuses,
                            alarm_sources,
                            acknowledged,
                            request_id,
                        )

                    # 各スレッドの実行結果を回収
                    for vcenter_name in configs.keys():
                        alarms = futures[vcenter_name].result()
                        Logging.info(f"{request_id} vCenter({vcenter_name})からのトリガー済みアラーム情報取得に成功")
                        all_alarms.extend(alarms)

                    # 全アラーム数を取得
                    total_alarm_count = len(all_alarms)

                    # オフセットと最大件数の調整
                    all_alarms = all_alarms[offset:]
                    if len(all_alarms) > max_results:
                        all_alarms = all_alarms[:max_results]

                except Exception as e:
                    Logging.error(f"{request_id} vCenter({vcenter_name})からのトリガー済みアラーム情報取得に失敗: {e}")

        return all_alarms, total_alarm_count

    @classmethod
    @Logging.func_logger
    def _get_alarms_from_vcenter(
        cls,
        vcenter_name: str,
        service_instances: dict,
        begin_time: str = None,
        end_time: str = None,
        days_ago_begin: int = None,
        days_ago_end: int = None,
        hours_ago_begin: int = None,
        hours_ago_end: int = None,
        statuses: List[str] = None,
        alarm_sources: List[str] = None,
        acknowledged: bool = None,
        request_id: str = None,
    ) -> list[AlarmResponseSchema]:
        """特定のvCenterからトリガー済みのアラーム一覧を取得"""

        results = []
        max_retrieve_alarms = int(
            os.getenv(
                "VLB_MAX_RETRIEVE_ALARMS_PER_VCENTER",
                cls.VLB_MAX_RETRIEVE_ALARMS_PER_VCENTER_DEFAULT,
            )
        )

        # 指定されたvCenterのService Instanceを取得
        if vcenter_name not in service_instances:
            raise HTTPException(status_code=404, detail=f"vCenter({vcenter_name}) not found")

        content = service_instances[vcenter_name].RetrieveContent()
        datacenter = content.rootFolder.childEntity[0]

        # 全トリガー済みアラームをリストで取得
        root_folder = content.rootFolder
        triggered_alarms = root_folder.triggeredAlarmState

        # 時間帯の指定がない場合、7日前からのトリガー済みのアラームを取得
        if begin_time:
            begin_time_obj = datetime.datetime.fromisoformat(begin_time).astimezone(datetime.timezone.utc)
        else:
            begin_time_obj = (datetime.datetime.now() - datetime.timedelta(days=7)).astimezone(datetime.timezone.utc)

        # 時間帯の指定がない場合、7日前からのイベントを取得
        if hours_ago_begin:
            begin_time_obj = (datetime.datetime.now() - datetime.timedelta(hours=hours_ago_begin)).astimezone(
                datetime.timezone.utc
            )
            Logging.info(f"{request_id} 時間帯の開始時間: {begin_time_obj}")
        elif days_ago_begin:
            begin_time_obj = (datetime.datetime.now() - datetime.timedelta(days=days_ago_begin)).astimezone(
                datetime.timezone.utc
            )
            Logging.info(f"{request_id} 時間帯の開始日: {begin_time_obj}")
        else:
            if begin_time:
                begin_time_obj = datetime.datetime.fromisoformat(begin_time).astimezone(datetime.timezone.utc)
            else:
                begin_time_obj = (datetime.datetime.now() - datetime.timedelta(days=7)).astimezone(
                    datetime.timezone.utc
                )

        # 時間帯の指定がない場合、現在までのイベントを取得
        if hours_ago_end:
            end_time_obj = (datetime.datetime.now() - datetime.timedelta(hours=hours_ago_end)).astimezone(
                datetime.timezone.utc
            )
            Logging.info(f"{request_id} 時間帯の終了時間: {end_time_obj}")
        elif days_ago_end:
            end_time_obj = (datetime.datetime.now() - datetime.timedelta(days=days_ago_end)).astimezone(
                datetime.timezone.utc
            )
            Logging.info(f"{request_id} 時間帯の終了日: {end_time_obj}")
        else:
            if end_time:
                end_time_obj = datetime.datetime.fromisoformat(end_time).astimezone(datetime.timezone.utc)
            else:
                end_time_obj = datetime.datetime.now().astimezone(datetime.timezone.utc)

        for alarm_state in triggered_alarms:
            if isinstance(alarm_state, vim.AlarmState):
                # ステータスの条件を指定した場合、マッチしないアラームをスキップ
                if statuses:
                    if not alarm_state.overallStatus in statuses:
                        continue
                # 確認済みかどうかの条件を指定した場合、マッチしないアラームをスキップ
                if acknowledged:
                    if not alarm_state.acknowledged == acknowledged:
                        continue
                # アラームソースの条件を指定した場合、マッチしないアラームをスキップ
                if alarm_sources:
                    if hasattr(alarm_state, "entity") and alarm_state.entity:
                        if not alarm_state.entity.name in alarm_sources:
                            continue
                alarm_time = alarm_state.time.astimezone(datetime.timezone.utc)
                if alarm_time >= begin_time_obj and alarm_time < end_time_obj:
                    alarm_info = cls._generate_alarm_info(datacenter, alarm_state, vcenter_name)
                    results.append(alarm_info)

        return results

    @classmethod
    @Logging.func_logger
    def _generate_alarm_info(cls, datacenter, alarm_state: vim.AlarmState, vcenter_name: str) -> AlarmResponseSchema:
        """アラーム情報を生成"""

        if hasattr(alarm_state, "entity") and alarm_state.entity:
            alarm_source = alarm_state.entity.name
        else:
            alarm_source = None

        ararm_info = {
            "vcenter": vcenter_name,
            "datacenter": datacenter.name,
            "name": alarm_state.alarm.info.name,
            "description": alarm_state.alarm.info.description,
            "status": alarm_state.overallStatus,
            "createdTime": alarm_state.time.isoformat(),
            "acknowledged": alarm_state.acknowledged,
            "acknowledgedTime": alarm_state.acknowledgedTime.isoformat() if alarm_state.acknowledgedTime else None,
            "alarmSource": alarm_source,
        }
        return AlarmResponseSchema(**ararm_info)
