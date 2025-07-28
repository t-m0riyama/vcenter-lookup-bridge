from pyVmomi import vim
from vcenter_lookup_bridge.utils.logging import Logging


class Helper(object):
    """vCenterオブジェクト取得用のヘルパークラス"""

    @classmethod
    @Logging.func_logger
    def get_object_by_name(cls, content, vimtype, name):
        """指定した名前のオブジェクトを取得"""

        obj = None
        cv = cls._create_container_view(content, vimtype)

        for child_object in cv.view:
            if name:
                if child_object.name == name:
                    obj = child_object
                    break
            else:
                obj = child_object
                break
        cv.Destroy()
        return obj

    @classmethod
    @Logging.func_logger
    def get_object_by_object_key(cls, content, vimtype, object_key):
        """指定したオブジェクトキーのオブジェクトを取得"""

        obj = None
        cv = cls._create_container_view(content=content, vimtypes=[vimtype])

        for child_object in cv.view:
            if object_key:
                match vimtype:
                    case vim.VirtualMachine:
                        object_key_prefix = "vim.VirtualMachine"
                    case vim.HostSystem:
                        object_key_prefix = "vim.HostSystem"
                    case vim.Datastore:
                        object_key_prefix = "vim.Datastore"
                    case vim.Network:
                        object_key_prefix = "vim.Network"
                    case vim.dvs.DistributedVirtualPortgroup:
                        object_key_prefix = "vim.dvs.DistributedVirtualPortgroup"

                if f"'{object_key_prefix}:{child_object._moId}'" == str(object_key):
                    obj = child_object
                    break
            else:
                obj = child_object
                break
        cv.Destroy()
        return obj

    @classmethod
    @Logging.func_logger
    def _create_container_view(cls, content, vimtypes):
        """ContainerViewを作成"""

        cv = content.viewManager.CreateContainerView(
            container=content.rootFolder,
            type=vimtypes,
            recursive=True,
        )
        return cv
