from pyVmomi import vim
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.vmware.helper import Helper


class Host(object):

    @classmethod
    def get_host_by_name(cls, content, host_name):
        result = None
        host = Helper.get_object_by_name(
            content=content,
            vimtype=[vim.HostSystem],
            name=host_name
        )
        if host is None: return result

        if isinstance(host, vim.HostSystem):
            host_info = cls._generate_host_info(host=host)
            result = host_info

        return result

    @classmethod
    def get_host_by_object_key(cls, content, object_key):
        result = None
        host = Helper.get_object_by_object_key(
            content=content,
            vimtype=vim.HostSystem,
            object_key=object_key
        )
        if host is None: return result

        if isinstance(host, vim.HostSystem):
            host_info = cls._generate_host_info(host=host)
            result = host_info

        return result

    @classmethod
    def _generate_host_info(cls, host):
        host_config = {
            "name": host.name,
            "moId": str(host),
            "tags": host.tag,
        }
        return host_config
