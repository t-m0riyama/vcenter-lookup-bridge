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


class Connector(object):
    # Const
    VCENTER_CONNECT_TIMEOUT_SEC_DEFAULT = 60
    VCENTER_CONNECT_RETRY_INTERVAL_SEC_DEFAULT = 30
    VCENTER_CONNECTION_POOL_TIMEOUT_SEC_DEFAULT = 3600
    VCENTER_HTTP_PROXY_HOST_DEFAULT  = "proxy.example.com"
    VCENTER_HTTP_PROXY_PORT_DEFAULT  = 8080

    @classmethod
    def _connect_vcenter(cls, config):
        try:
            vcenter_connect_timeout = int(os.getenv(
                "VLB_VCENTER_CONNECT_TIMEOUT", cls.VCENTER_CONNECT_TIMEOUT_SEC_DEFAULT))
            vcenter_connection_pool_timeout = int(os.getenv(
                "VLB_VCENTER_CONNECTION_POOL_TIMEOUT", cls.VCENTER_CONNECTION_POOL_TIMEOUT_SEC_DEFAULT))
            vcenter_proxy_enabled = bool(setuptools.distutils.util.strtobool(os.getenv(
                "VLB_VCENTER_HTTP_PROXY_ENABLED", "False")))
            vcenter_http_proxy_host = os.getenv(
                "VLB_VCENTER_HTTP_PROXY_HOST", cls.VCENTER_HTTP_PROXY_HOST_DEFAULT)
            vcenter_http_proxy_port = int(os.getenv(
                "VLB_VCENTER_HTTP_PROXY_PORT", cls.VCENTER_HTTP_PROXY_PORT_DEFAULT))

            if vcenter_proxy_enabled:
                Logging.info(f"HTTPプロキシを経由して、vCenter({config['hostname']})に接続します")
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
                f"vCenter({config['hostname']})接続時にタイムアウトが発生しました(STATUS/{cs.EXIT_ERR_VCENTER_CONNECT_TIMEOUT_FAIL})"
            )
            raise TimeoutError(e)
        except ConnectionRefusedError as e:
            Logging.error(
                f"vCenter({config['hostname']})に接続を拒否されました(STATUS/{cs.EXIT_ERR_VCENTER_CONNECT_REFUSED_FAIL})"
            )
            raise ConnectionRefusedError(e)
        except socket.gaierror as e:
            Logging.error(
                f"vCenter({config['hostname']})に接続時にホスト名の解決に失敗しました(STATUS/{cs.EXIT_ERR_VCENTER_CONNECT_HOSTNAMRE_RESOLVE_FAIL})"
            )
            raise socket.gaierror(e)
        except pyVmomi.vim.fault.InvalidLogin as e:
            Logging.error(
                f"vCenter({config['hostname']})に接続時にログインに失敗しました(STATUS/{cs.EXIT_ERR_VCENTER_CONNECT_LOGIN_FAIL})"
            )
            Logging.error(e)
            # 認証情報が間違っている場合は、永続的なエラーとして異常終了する
            sys.exit(cs.EXIT_ERR_VCENTER_CONNECT_LOGIN_FAIL)
        except Exception as e:
            Logging.error(
                f"vCenter({config['hostname']})に接続時に不明なエラーが発生しました(STATUS/{cs.EXIT_ERR_VCENTER_CONNECT_UNKNOWN_FAIL})"
            )
            raise e

        atexit.register(cls._disconnect_vcenter, si)
        return si

    @classmethod
    def _disconnect_vcenter(cls, si):
        Disconnect(si)

    @classmethod
    def get_service_instances(cls, configs):
        vcenter_connect_retry_interval = int(os.getenv("VLB_VCENTER_CONNECT_RETRY_INTERVAL_SEC", cls.VCENTER_CONNECT_RETRY_INTERVAL_SEC_DEFAULT))

        # VMware WS APIのService Instanceが作成されていない場合、インスタンスを保持するリストを初期化する
        if not hasattr(g, 'service_instances'):
            g.service_instances = {}

        # テスト環境の場合はモックを返す
        if os.getenv("TESTING") == "1":
            from unittest.mock import Mock
            for config_key in configs.keys():
                if config_key not in g.service_instances:
                    mock_si = Mock()
                    mock_si.CurrentTime.return_value = True
                    g.service_instances[config_key] = mock_si
            return g.service_instances

        for config_key in configs.keys():
            try:
                if config_key not in g.service_instances:
                    raise Exception(f"vCenter({configs[config_key]['hostname']})は未接続な状態です")

                current_time = g.service_instances[config_key].CurrentTime()
            except:
                # TODO: 複数のvCenterに接続し、Service Instanceを複数利用する場合の処理を実装する
                # 一部のvCenterに接続できない場合は、一定時間で接続を諦めた上で、
                # 不安定な接続としてマークし、時間をおいて再接続を試みる再接続を試みる
                while True:
                    try:
                        si = cls._connect_vcenter(config=configs[config_key])
                        break
                    except Exception as e:
                        Logging.error(f"vCenter({configs[config_key]['hostname']})への（再）接続に失敗しました")
                        Logging.error(f"vCenter({configs[config_key]['hostname']})接続エラー: {e}")
                        time.sleep(vcenter_connect_retry_interval)
                g.service_instances[config_key] = si
                Logging.info(f"vCenter({configs[config_key]['hostname']})への（再）接続に成功しました")
        return g.service_instances

    async def get_vmware_content():
        service_instances = Connector.get_service_instances(
            configs=g.vcenter_configurations,
        )

        # TODO: 複数のvCenterに接続し、Service Instanceを複数利用する場合の処理を実装する
        # 今回は1つ目のService Instanceのみ利用する
        config_keys = list(g.vcenter_configurations.keys())
        return service_instances[config_keys[0]].RetrieveContent()
