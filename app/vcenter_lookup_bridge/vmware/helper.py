from pyVmomi import vim
from vcenter_lookup_bridge.utils.logging import Logging


class Helper(object):

    @classmethod
    def get_object_by_name(cls, content, vimtype, name):
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
        return obj

    @classmethod
    def get_object_by_object_key(cls, content, vimtype, object_key):
        obj = None
        cv = cls._create_container_view(content=content, vimtypes=[vimtype])

        for child_object in cv.view:
            if object_key:
                match vimtype:
                    case vim.VirtualMachine:
                        object_key_prefix = 'vim.VirtualMachine'
                    case vim.HostSystem:
                        object_key_prefix = 'vim.HostSystem'
                    case vim.Datastore:
                        object_key_prefix = 'vim.Datastore'
                    case vim.Network:
                        object_key_prefix = 'vim.Network'

                if f"'{object_key_prefix}:{child_object._moId}'" == str(object_key):
                    obj = child_object
                    break
            else:
                obj = child_object
                break
        return obj

    @classmethod
    def _create_container_view(cls, content, vimtypes):
        cv = content.viewManager.CreateContainerView(
            container=content.rootFolder,
            type=vimtypes,
            recursive=True,
        )
        return cv
