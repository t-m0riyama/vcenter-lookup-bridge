from pyVmomi import vim
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.schemas.datastore_parameter import DatastoreResponseSchema
from vcenter_lookup_bridge.vmware.host import Host
from vcenter_lookup_bridge.vmware.tag import Tag
import vcenter_lookup_bridge.vmware.instances as g


class Datastore(object):

    @classmethod
    def get_datastores_by_tags(
        cls,
        content,
        tag_category: str,
        tags: list[str],
        offset: int=0,
        max_results: int=100,
    ) -> list[DatastoreResponseSchema]:
        results = []
        datastore_count = 0

        cv = content.viewManager.CreateContainerView(
            container=content.rootFolder,
            type=[vim.Datastore],
            recursive=True
        )
        datastores = cv.view
        datastore_tags = Tag.get_all_datastore_tags(configs=g.vcenter_configurations)

        for datastore in datastores:
            # offsetまでスキップ
            if datastore_count < offset:
                datastore_count += 1
                continue
            # max_resultsまで取得
            if datastore_count >= offset + max_results:
                break

            if isinstance(datastore, vim.Datastore):
                for datastore_name in datastore_tags.keys():
                    if datastore.name == datastore_name:
                        if tag_category in datastore_tags[datastore_name]:
                            datastore_config = cls._generate_datastore_info(datastore=datastore, content=content)
                            datastore_config['tag_category'] = tag_category
                            datastore_config['tags'] = datastore_tags[datastore_name][tag_category]

                            for attached_tag in datastore_tags[datastore_name][tag_category]:
                                if str(attached_tag) in tags:
                                    results.append(datastore_config)
                                    datastore_count += 1
        return results

    @classmethod
    def _generate_datastore_info(cls, datastore, content):
        if isinstance(datastore, vim.Datastore):
            # データストアをマウントしているホストの情報を取得
            hosts = []
            for host in datastore.host:
                hosts.append((Host.get_host_by_object_key(content=content, object_key=host.key))['name'])

            datastore_config = {
                        "name": datastore.name,
                        "tags": datastore.tag,
                        "type": str(datastore.summary.type),
                        "capacityGB": int(datastore.summary.capacity / 1024 ** 3),
                        "freeSpaceGB": int(datastore.summary.freeSpace / 1024 ** 3),
                        "hosts": hosts,
            }
            return datastore_config
