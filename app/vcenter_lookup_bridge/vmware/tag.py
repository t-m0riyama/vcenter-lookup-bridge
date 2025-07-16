import requests
import urllib3
from vcenter_lookup_bridge.utils.logging import Logging
from vmware.vapi.vsphere.client import create_vsphere_client, VsphereClient

# SSL関連の警告出力を抑制
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Tag(object):
    """タグ情報を取得するクラス"""

    # @classmethod
    # def get_vm_tags(cls, configs, vm_name: str) -> dict:
    #     vm_tags = cls.get_all_vm_tags(configs=configs)
    #     if vm_name not in vm_tags:
    #         return {}
    #     return vm_tags[vm_name]

    # @classmethod
    # def get_all_vm_tags(cls, configs) -> dict:
    #     clients = cls._create_clients(configs=configs)
    #     cat_dict, tag_dict = cls._generate_all_tag_dict(clients=clients)
    #     return cls._generate_object_tag_dict(
    #         clients=clients, cat_dict=cat_dict, tag_dict=tag_dict, object_type="VirtualMachine"
    #     )

    @classmethod
    def get_all_datastore_tags(cls, config) -> dict:
        client = cls._create_client(config=config)
        cat_dict, tag_dict = cls._generate_all_tag_dict(client=client)
        return cls._generate_object_tag_dict(
            client=client, cat_dict=cat_dict, tag_dict=tag_dict, object_type="Datastore"
        )

    @classmethod
    def get_all_portgroup_tags(cls, config) -> dict:
        client = cls._create_client(config=config)
        cat_dict, tag_dict = cls._generate_all_tag_dict(client=client)
        return cls._generate_object_tag_dict(client=client, cat_dict=cat_dict, tag_dict=tag_dict, object_type="Network")

    @classmethod
    def _create_client(cls, config) -> VsphereClient:
        session = requests.session()
        session.verify = not config["ignore_ssl_cert_verify"]
        client = create_vsphere_client(
            server=config["hostname"],
            username=config["username"],
            password=config["password"],
            session=session,
        )
        return client

    @classmethod
    def _generate_object_tag_dict(cls, client, cat_dict, tag_dict, object_type) -> dict:
        object_tags = {}

        tag_search_objs = cls._generate_tag_search_object(object_type, client)
        for tagged_object in client.tagging.TagAssociation.list_attached_tags_on_objects(tag_search_objs):
            cat_tag_dict = {}
            for tag_id in tagged_object.tag_ids:
                cat_name = cat_dict[tag_dict[tag_id].category_id]
                if cat_name not in cat_tag_dict:
                    cat_tag_dict[cat_name] = []
                cat_tag_dict[cat_name].append(tag_dict[tag_id].name)
            object_name = cls._get_object_name_by_object_id(object_type, client, tagged_object)
            object_tags[object_name] = cat_tag_dict
        return object_tags

    @classmethod
    def _get_object_name_by_object_id(cls, object_type, client, tagged_object) -> str:
        match object_type:
            case "VirtualMachine":
                object_name = client.vcenter.VM.get(tagged_object.object_id.id).name
            case "Datastore":
                object_name = client.vcenter.Datastore.get(tagged_object.object_id.id).name
            case "Network":
                objects = client.vcenter.Network.list()
                for object in objects:
                    if object.network == tagged_object.object_id.id:
                        object_name = object.name
                        break
        return object_name

    @classmethod
    def _generate_tag_search_object(cls, object_type, client) -> list[dict]:
        match object_type:
            case "VirtualMachine":
                objects = client.vcenter.VM.list()
                tag_search_objs = [{"id": v.vm, "type": object_type} for v in objects]
            case "Datastore":
                objects = client.vcenter.Datastore.list()
                tag_search_objs = [{"id": v.datastore, "type": object_type} for v in objects]
            case "Network":
                objects = client.vcenter.Network.list()
                tag_search_objs = [{"id": v.network, "type": object_type} for v in objects]
        return tag_search_objs

    @classmethod
    def _generate_all_tag_dict(cls, client) -> tuple[dict, dict]:
        cat_dict = {}
        tag_dict = {}

        cls._generate_tag_dict(cat_dict, tag_dict, client)
        return cat_dict, tag_dict

    @classmethod
    def _generate_tag_dict(cls, cat_dict, tag_dict, client) -> None:
        for id in client.tagging.Category.list():
            cat = client.tagging.Category.get(id)
            cat_dict[cat.id] = cat.name

        for id in client.tagging.Tag.list():
            tag = client.tagging.Tag.get(id)
            tag_dict[id] = tag
