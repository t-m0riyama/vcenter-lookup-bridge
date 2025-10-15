import datetime
import os
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException
from pyVmomi import vim
from vcenter_lookup_bridge.schemas.event_parameter import EventResponseSchema
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.vmware.helper import Helper


class Event(object):
    """イベント情報を取得するクラス"""

    # Const
    VLB_MAX_RETRIEVE_VCENTER_OBJECTS_DEFAULT = 1000
    VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT = 10
    VLB_MAX_RETRIEVE_EVENTS_PER_VCENTER_DEFAULT = 1000

    @classmethod
    @Logging.func_logger
    def get_events_from_all_vcenters(
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
        event_types: List[str] = None,
        event_sources: List[str] = None,
        user_names: List[str] = None,
        ip_addresses: List[str] = None,
        offset=0,
        max_results=100,
        request_id: str = None,
    ) -> tuple[list[EventResponseSchema], int]:
        """全vCenterからイベント一覧を取得"""

        all_events = []
        total_event_count = 0
        max_vcenter_web_service_worker_threads = int(
            os.getenv(
                "VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS",
                cls.VLB_MAX_VCENTER_WEB_SERVICE_WORKER_THREADS_DEFAULT,
            )
        )

        if vcenter_name:
            # vCenterを指定した場合、指定したvCenterからイベント一覧を取得
            try:
                events = cls._get_events_from_vcenter(
                    vcenter_name=vcenter_name,
                    service_instances=service_instances,
                    begin_time=begin_time,
                    end_time=end_time,
                    days_ago_begin=days_ago_begin,
                    days_ago_end=days_ago_end,
                    hours_ago_begin=hours_ago_begin,
                    hours_ago_end=hours_ago_end,
                    event_types=event_types,
                    event_sources=event_sources,
                    user_names=user_names,
                    ip_addresses=ip_addresses,
                    request_id=request_id,
                )
                Logging.info(f"{request_id} vCenter({vcenter_name})からのイベント情報取得に成功")
                all_events.extend(events)
                total_event_count = len(all_events)
            except ValueError as e:
                raise HTTPException(status_code=422, detail=f"日付/時刻パラメータの書式が不正です。")
            except Exception as e:
                Logging.error(f"{request_id} vCenter({vcenter_name})からのイベント情報取得に失敗: {e}")
        else:
            # vCenterを指定しない場合、すべてのvCenterからイベント一覧を取得
            futures = {}
            with ThreadPoolExecutor(max_workers=max_vcenter_web_service_worker_threads) as executor:
                try:
                    # 各vCenterからイベント一覧を取得するスレッドを作成
                    for vcenter_name in configs.keys():
                        futures[vcenter_name] = executor.submit(
                            cls._get_events_from_vcenter,
                            vcenter_name,
                            service_instances,
                            begin_time,
                            end_time,
                            days_ago_begin,
                            days_ago_end,
                            hours_ago_begin,
                            hours_ago_end,
                            event_types,
                            event_sources,
                            user_names,
                            ip_addresses,
                            request_id,
                        )

                    # 各スレッドの実行結果を回収
                    for vcenter_name in configs.keys():
                        events = futures[vcenter_name].result()
                        Logging.info(f"{request_id} vCenter({vcenter_name})からのイベント情報取得に成功")
                        all_events.extend(events)

                    # 全イベント数を取得
                    total_event_count = len(all_events)

                    # オフセットと最大件数の調整
                    all_events = all_events[offset:]
                    if len(all_events) > max_results:
                        all_events = all_events[:max_results]

                except ValueError as e:
                    raise HTTPException(status_code=422, detail=f"日付/時刻パラメータの書式が不正です。")
                except Exception as e:
                    Logging.error(f"{request_id} vCenter({vcenter_name})からのイベント情報取得に失敗: {e}")

        return all_events, total_event_count

    @classmethod
    @Logging.func_logger
    def _get_events_from_vcenter(
        cls,
        vcenter_name: str,
        service_instances: dict,
        begin_time: str = None,
        end_time: str = None,
        days_ago_begin: int = None,
        days_ago_end: int = None,
        hours_ago_begin: int = None,
        hours_ago_end: int = None,
        event_types: List[str] = None,
        event_sources: List[str] = None,
        user_names: List[str] = None,
        ip_addresses: List[str] = None,
        request_id: str = None,
    ) -> list[EventResponseSchema]:
        """特定のvCenterからイベント一覧を取得"""

        results = []
        max_retrieve_events = int(
            os.getenv(
                "VLB_MAX_RETRIEVE_EVENTS_PER_VCENTER",
                cls.VLB_MAX_RETRIEVE_EVENTS_PER_VCENTER_DEFAULT,
            )
        )

        # 指定されたvCenterのService Instanceを取得
        if vcenter_name not in service_instances:
            raise HTTPException(status_code=404, detail=f"vCenter({vcenter_name}) not found")

        content = service_instances[vcenter_name].RetrieveContent()
        datacenter = content.rootFolder.childEntity[0]

        event_mgr = content.eventManager
        filter_spec = vim.event.EventFilterSpec()
        time_filter = vim.event.EventFilterSpec.ByTime()

        # 時間帯の指定がない場合、7日前からのイベントを取得
        if hours_ago_begin:
            time_filter.beginTime = (datetime.datetime.now() - datetime.timedelta(hours=hours_ago_begin)).astimezone(
                datetime.timezone.utc
            )
        elif days_ago_begin:
            time_filter.beginTime = (datetime.datetime.now() - datetime.timedelta(days=days_ago_begin)).astimezone(
                datetime.timezone.utc
            )
        else:
            if begin_time:
                time_filter.beginTime = datetime.datetime.fromisoformat(begin_time)
            else:
                time_filter.beginTime = datetime.datetime.now() - datetime.timedelta(days=7)

        # 時間帯の指定がない場合、現在までのイベントを取得
        if hours_ago_end:
            time_filter.endTime = (datetime.datetime.now() - datetime.timedelta(hours=hours_ago_end)).astimezone(
                datetime.timezone.utc
            )
        elif days_ago_end:
            time_filter.endTime = (datetime.datetime.now() - datetime.timedelta(days=days_ago_end)).astimezone(
                datetime.timezone.utc
            )
        else:
            if end_time:
                time_filter.endTime = datetime.datetime.fromisoformat(end_time)
            else:
                time_filter.endTime = datetime.datetime.now()

        filter_spec.time = time_filter

        # イベントタイプの指定をした場合、該当イベントのみ取得するフィルタを設定
        if event_types:
            filter_spec.eventTypeId = event_types

        # ユーザ名を指定した場合、ユーザフィルタを指定
        if user_names:
            user_filter = vim.event.EventFilterSpec.ByUsername()
            user_filter.userList = user_names
            filter_spec.userName = user_filter
        collector = event_mgr.CreateCollectorForEvents(filter=filter_spec)
        events = collector.ReadNextEvents(max_retrieve_events)

        for event in events:
            if isinstance(event, vim.Event):
                event_info = cls._generate_event_info(datacenter, event, vcenter_name)
                # IPアドレスの条件を指定した場合、マッチしないイベントをスキップ
                if ip_addresses:
                    if event_info.ipAddress not in ip_addresses:
                        continue
                # イベントソースの条件を指定した場合、マッチしないイベントをスキップ
                if event_sources:
                    if event_info.eventSource not in event_sources:
                        continue
                results.append(event_info)
        return results

    @classmethod
    @Logging.func_logger
    def _generate_event_info(cls, datacenter, event: vim.Event, vcenter_name: str) -> EventResponseSchema:
        """イベント情報を生成"""

        if hasattr(event, "entity") and event.entity is not None:
            event_source = event.entity.name
        elif hasattr(event, "host") and event.host is not None:
            event_source = event.host.name
        elif hasattr(event, "vm") and event.vm is not None:
            event_source = event.vm.name
        else:
            event_source = None

        if hasattr(event, "ipAddress") and event.ipAddress:
            ip_address = event.ipAddress
        else:
            ip_address = None

        event_info = {
            "vcenter": vcenter_name,
            "datacenter": datacenter.name,
            "eventType": type(event).__name__.replace("vim.event.", ""),
            "message": event.fullFormattedMessage,
            "createdTime": event.createdTime.isoformat(),
            "eventSource": event_source,
            "ipAddress": ip_address,
            "userName": event.userName,
        }
        return EventResponseSchema(**event_info)
