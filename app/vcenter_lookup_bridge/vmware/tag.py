import requests
import urllib3
from vcenter_lookup_bridge.utils.logging import Logging
from vmware.vapi.vsphere.client import create_vsphere_client

# SSL関連の警告出力を抑制
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Tag(object):

    @classmethod
    def get_vm_tags(cls, configs, vm_name: str) -> dict:
        vm_tags = cls.get_all_vm_tags(configs=configs)
        if vm_name not in vm_tags:
            return {}
        return vm_tags[vm_name]

    @classmethod
    def get_all_vm_tags(cls, configs) -> dict:
        clients = cls._create_clients(configs=configs)
        cat_dict, tag_dict = cls._generate_tag_dict(clients=clients)
        return cls._generate_object_tag_dict(clients=clients, cat_dict=cat_dict, tag_dict=tag_dict, object_type='VirtualMachine')

    def get_datastore_tags(cls, configs, datastore_name: str) -> dict:
        datastore_tags = cls.get_all_datastore_tags(configs=configs)
        if datastore_name not in datastore_tags:
            return {}
        return datastore_tags[datastore_name]

    @classmethod
    def get_all_datastore_tags(cls, configs) -> dict:
        clients = cls._create_clients(configs=configs)
        cat_dict, tag_dict = cls._generate_tag_dict(clients=clients)
        return cls._generate_object_tag_dict(clients=clients, cat_dict=cat_dict, tag_dict=tag_dict, object_type='Datastore')

    @classmethod
    def get_portgroup_tags(cls, configs, portgroup_name: str) -> dict:
        portgroup_tags = cls.get_all_portgroup_tags(configs=configs)
        if portgroup_name not in portgroup_tags:
            return {}
        return portgroup_tags[portgroup_name]

    @classmethod
    def get_all_portgroup_tags(cls, configs) -> dict:
        clients = cls._create_clients(configs=configs)
        cat_dict, tag_dict = cls._generate_tag_dict(clients=clients)
        return cls._generate_object_tag_dict(clients=clients, cat_dict=cat_dict, tag_dict=tag_dict, object_type='Network')

    @classmethod
    def _create_clients(cls, configs):
        clients = []

        for config_key in configs.keys():
            session = requests.session()
            session.verify = not configs[config_key]["ignore_ssl_cert_verify"]
            client = create_vsphere_client(
                server=configs[config_key]["hostname"],
                username=configs[config_key]["username"],
                password=configs[config_key]["password"],
                session=session,
            )
            if client is not None:
                clients.append(client)
        return clients

    @classmethod
    def _generate_object_tag_dict(cls, clients, cat_dict, tag_dict, object_type):
        object_tags = {}

        for client in clients:
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
    def _get_object_name_by_object_id(cls, object_type, client, tagged_object):
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
    def _generate_tag_search_object(cls, object_type, client):
        match object_type:
            case "VirtualMachine":
                objects = client.vcenter.VM.list()
                tag_search_objs = [{'id': v.vm, 'type': object_type} for v in objects]
            case "Datastore":
                objects = client.vcenter.Datastore.list()
                tag_search_objs = [{'id': v.datastore, 'type': object_type} for v in objects]
            case "Network":
                objects = client.vcenter.Network.list()
                tag_search_objs = [{'id': v.network, 'type': object_type} for v in objects]
        return tag_search_objs

    @classmethod
    def _generate_tag_dict(cls, clients):
        cat_dict = {}
        tag_dict = {}

        for client in clients:
            for id in client.tagging.Category.list():
                cat = client.tagging.Category.get(id)
                cat_dict[cat.id] = cat.name

            for id in client.tagging.Tag.list():
                tag = client.tagging.Tag.get(id)
                tag_dict[id] = tag
        return cat_dict, tag_dict
