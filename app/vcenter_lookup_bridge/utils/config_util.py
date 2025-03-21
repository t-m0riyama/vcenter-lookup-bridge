import yaml

__version__ = "1.0"


class ConfigUtil(object):
    @classmethod
    def parse_config(cls, config_file):
        return yaml.safe_load(open(config_file, 'r'))
