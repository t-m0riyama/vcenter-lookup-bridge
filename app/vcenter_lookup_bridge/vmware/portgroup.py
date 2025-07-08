import sys

import vcenter_lookup_bridge.vmware.instances as g
from pyVmomi import vim
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.vmware.tag import Tag


class Portgroup(object):
    """ポートグループ情報を取得するクラス"""

    @classmethod
    def get_portgroups_by_tags(
        cls,
        content,
        tag_category: str,
        tags: list[str],
        offset: int = 0,
        max_results: int = 100,
    ) -> list:
        results = []
        portgroup_count = 0

        cv = content.viewManager.CreateContainerView(container=content.rootFolder, type=[vim.Network], recursive=True)
        portgroups = cv.view
        portgroup_tags = Tag.get_all_portgroup_tags(configs=g.vcenter_configurations)

        if portgroups is None:
            return results
        for portgroup in portgroups:
            # offsetまでスキップ
            if portgroup_count < offset:
                portgroup_count += 1
                continue
            # max_resultsまで取得
            if portgroup_count >= offset + max_results:
                break

            if isinstance(portgroup, vim.Network):
                for portgroup_name in portgroup_tags.keys():
                    if portgroup.name == portgroup_name:
                        if tag_category in portgroup_tags[portgroup_name]:
                            portgroup_config = cls._generate_portgroup_info(portgroup=portgroup, content=content)
                            portgroup_config["tag_category"] = tag_category
                            portgroup_config["tags"] = portgroup_tags[portgroup_name][tag_category]

                            for attached_tag in portgroup_tags[portgroup_name][tag_category]:
                                if str(attached_tag) in tags:
                                    results.append(portgroup_config)
                                    portgroup_count += 1
        return results

    @classmethod
    def _generate_portgroup_info(cls, portgroup, content):
        if isinstance(portgroup, vim.Network):
            # ポートグループを利用可能なESXiホストの情報を取得
            hosts = []
            for host in portgroup.host:
                hosts.append(host.name)

            portgroup_config = {
                "name": portgroup.name,
                "vcenter": "not_set",
                "hosts": hosts,
            }
            return portgroup_config
