import atexit
import os
import socket
import sys
import time
import pyVmomi
import setuptools
import vcenter_lookup_bridge.vmware.instances as g
from pyVim.connect import Disconnect, SmartConnect
from vcenter_lookup_bridge.utils.constants import Constants as cs
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.vmware.vcenter_ws_session_managr import VCenterWSSessionManager


class Connector(object):
    """vCenter接続(Web Service API)を管理するクラス"""

    # Const
    VLB_VCENTER_CONNECT_TIMEOUT_SEC_DEFAULT = 20
    VLB_VCENTER_CONNECT_RETRY_INTERVAL_SEC_DEFAULT = 20
    VLB_VCENTER_CONNECT_RETRY_MAX_COUNT_DEFAULT = 2
    VLB_VCENTER_CONNECTION_POOL_TIMEOUT_SEC_DEFAULT = 3600
    VLB_VCENTER_HTTP_PROXY_HOST_DEFAULT = "proxy.example.com"
    VLB_VCENTER_HTTP_PROXY_PORT_DEFAULT = 8080

    @classmethod
    @Logging.func_logger
    def _connect_vcenter(cls, config, vcenter_name):
        try:
            vcenter_connect_timeout = int(
                os.getenv(
                    "VLB_VCENTER_CONNECT_TIMEOUT_SEC",
                    cls.VLB_VCENTER_CONNECT_TIMEOUT_SEC_DEFAULT,
                )
            )
            vcenter_connection_pool_timeout = int(
                os.getenv(
                    "VLB_VCENTER_CONNECTION_POOL_TIMEOUT_SEC",
                    cls.VLB_VCENTER_CONNECTION_POOL_TIMEOUT_SEC_DEFAULT,
                )
            )
            vcenter_proxy_enabled = bool(
                setuptools.distutils.util.strtobool(os.getenv("VLB_VCENTER_HTTP_PROXY_ENABLED", "False"))
            )
            vcenter_http_proxy_host = os.getenv("VLB_VCENTER_HTTP_PROXY_HOST", cls.VLB_VCENTER_HTTP_PROXY_HOST_DEFAULT)
            vcenter_http_proxy_port = int(
                os.getenv("VLB_VCENTER_HTTP_PROXY_PORT", cls.VLB_VCENTER_HTTP_PROXY_PORT_DEFAULT)
            )

            if vcenter_proxy_enabled:
                Logging.info(
                    f"HTTPプロキシを経由して、vCenter({vcenter_name} - {config['hostname']}:{config['port']})に接続します"
                )
                Logging.info(f"HTTPプロキシ: {vcenter_http_proxy_host}:{vcenter_http_proxy_port}")
                si = SmartConnect(
                    host=config["hostname"],
                    port=config["port"],
                    user=config["username"],
                    pwd=config["password"],
                    httpProxyHost=vcenter_http_proxy_host,
                    httpProxyPort=vcenter_http_proxy_port,
                    disableSslCertValidation=config["ignore_ssl_cert_verify"],
                    httpConnectionTimeout=vcenter_connect_timeout,
                    connectionPoolTimeout=vcenter_connection_pool_timeout,
                )
            else:
                si = SmartConnect(
                    host=config["hostname"],
                    port=config["port"],
                    user=config["username"],
                    pwd=config["password"],
                    disableSslCertValidation=config["ignore_ssl_cert_verify"],
                    httpConnectionTimeout=vcenter_connect_timeout,
                    connectionPoolTimeout=vcenter_connection_pool_timeout,
                )
        except TimeoutError as e:
            Logging.error(
                f"vCenter({vcenter_name} - {config['hostname']}:{config['port']})接続時にタイムアウトが発生しました(STATUS/{cs.EXIT_ERR_VCENTER_CONNECT_TIMEOUT_FAIL})"
            )
            raise TimeoutError(e)
        except ConnectionRefusedError as e:
            Logging.error(
                f"vCenter({vcenter_name} - {config['hostname']}:{config['port']})に接続を拒否されました(STATUS/{cs.EXIT_ERR_VCENTER_CONNECT_REFUSED_FAIL})"
            )
            raise ConnectionRefusedError(e)
        except socket.gaierror as e:
            Logging.error(
                f"vCenter({vcenter_name} - {config['hostname']}:{config['port']})に接続時にホスト名の解決に失敗しました(STATUS/{cs.EXIT_ERR_VCENTER_CONNECT_HOSTNAMRE_RESOLVE_FAIL})"
            )
            raise socket.gaierror(e)
        except pyVmomi.vim.fault.InvalidLogin as e:
            Logging.error(
                f"vCenter({vcenter_name} - {config['hostname']}:{config['port']})に接続時にログインに失敗しました(STATUS/{cs.EXIT_ERR_VCENTER_CONNECT_LOGIN_FAIL})"
            )
            Logging.error(e)
            # 認証情報が間違っている場合は、永続的なエラーとして異常終了する
            sys.exit(cs.EXIT_ERR_VCENTER_CONNECT_LOGIN_FAIL)
        except Exception as e:
            Logging.error(
                f"vCenter({vcenter_name} - {config['hostname']}:{config['port']})に接続時に不明なエラーが発生しました(STATUS/{cs.EXIT_ERR_VCENTER_CONNECT_UNKNOWN_FAIL})"
            )
            raise e

        atexit.register(cls._disconnect_vcenter, si)
        return si

    @classmethod
    @Logging.func_logger
    def _disconnect_vcenter(cls, si):
        Disconnect(si)

    @classmethod
    @Logging.func_logger
    def _connect_vcenter_with_redis(cls):
        redis = VCenterWSSessionManager.initialize()
        VCenterWSSessionManager.set_vcenter_ws_session(
            redis=redis,
            vcenter_name="vcenter8-01",
            status=VCenterWSSessionManager.VCENTER_STATUS_ALIVE,
        )
        status = VCenterWSSessionManager.get_vcenter_ws_session(redis=redis, vcenter_name="vcenter8-01")
        return status

    @classmethod
    @Logging.func_logger
    def get_service_instances(cls):
        configs = g.vcenter_configurations
        vcenter_connect_retry_interval = int(
            os.getenv(
                "VLB_VCENTER_CONNECT_RETRY_INTERVAL_SEC",
                cls.VLB_VCENTER_CONNECT_RETRY_INTERVAL_SEC_DEFAULT,
            )
        )
        vcenter_connect_retry_max_count = int(
            os.getenv(
                "VLB_VCENTER_CONNECT_RETRY_MAX_COUNT",
                cls.VLB_VCENTER_CONNECT_RETRY_MAX_COUNT_DEFAULT,
            )
        )

        # VMware WS APIのService Instanceのリストが作成されていない場合、インスタンスを保持するリストを初期化する
        if not hasattr(g, "service_instances"):
            Logging.warning(f"vCenter Web Service APIのService Instanceを保持するリストを初期化します。")
            g.service_instances = {}

        # テスト環境の場合はモックを返す
        if os.getenv("TESTING") == "1":
            from unittest.mock import Mock

            for vcenter_name in configs.keys():
                if vcenter_name not in g.service_instances:
                    mock_si = Mock()
                    mock_si.CurrentTime.return_value = True
                    g.service_instances[vcenter_name] = mock_si
            return g.service_instances

        redis = VCenterWSSessionManager.initialize()
        for vcenter_name in configs.keys():
            connection_retry_count = 0
            # ダウン状態のvCenterについては、接続を試みない
            if VCenterWSSessionManager.is_dead_vcenter_ws_session(redis=redis, vcenter_name=vcenter_name):
                continue

            try:
                # 作成済みのService Instanceに対し、正常にリクエストを行えるかどうかを検査
                if vcenter_name not in g.service_instances:
                    raise Exception(f"vCenter({vcenter_name}) のService Instanceが未作成です。")

                current_time = g.service_instances[vcenter_name].CurrentTime()
                VCenterWSSessionManager.set_vcenter_ws_session(
                    redis=redis,
                    vcenter_name=vcenter_name,
                    status=VCenterWSSessionManager.VCENTER_STATUS_ALIVE,
                )
            except Exception as e:
                # 一部のvCenterに接続できない場合、かつリトライ上限を超過した際は接続を諦めた上で、
                # ダウン状態としてマークし、時間をおいて再接続を試みる
                Logging.warning(
                    f"vCenter({vcenter_name} - {configs[vcenter_name]['hostname']}:{configs[vcenter_name]['port']})は未接続です。再接続を試行します。"
                )
                while True:
                    try:
                        si = cls._connect_vcenter(config=configs[vcenter_name], vcenter_name=vcenter_name)
                        current_time = si.CurrentTime()
                        g.service_instances[vcenter_name] = si
                        VCenterWSSessionManager.set_vcenter_ws_session(
                            redis=redis,
                            vcenter_name=vcenter_name,
                            status=VCenterWSSessionManager.VCENTER_STATUS_ALIVE,
                        )
                        Logging.info(
                            f"vCenter({vcenter_name} - {configs[vcenter_name]['hostname']}:{configs[vcenter_name]['port']})への（再）接続に成功しました。"
                        )
                        break
                    except Exception as e:
                        connection_retry_count += 1
                        Logging.error(
                            f"vCenter({vcenter_name} - {configs[vcenter_name]['hostname']}:{configs[vcenter_name]['port']})への（再）接続に失敗しました"
                        )
                        Logging.error(
                            f"vCenter({vcenter_name} - {configs[vcenter_name]['hostname']}:{configs[vcenter_name]['port']})接続エラー: {e}"
                        )

                        if connection_retry_count >= vcenter_connect_retry_max_count:
                            # 最大リトライ回数に達した場合、ダウン状態としてマーク
                            VCenterWSSessionManager.set_vcenter_ws_session(
                                redis=redis,
                                vcenter_name=vcenter_name,
                                status=VCenterWSSessionManager.VCENTER_STATUS_DEAD,
                            )
                            Logging.error(
                                f"vCenter({vcenter_name} - {configs[vcenter_name]['hostname']}:{configs[vcenter_name]['port']})への（再）接続に失敗しました。最大リトライ回数に達したため、ダウンした接続としてマークしました"
                            )
                            break
                        time.sleep(vcenter_connect_retry_interval)
        return g.service_instances
