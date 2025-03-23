from threading import Lock


class VCenterConfigManager:
    """vCenterの設定を管理するシングルトンクラス"""
    _instance = None
    _lock = Lock()
    _vcenter_configurations = {}

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            with self._lock:
                if not hasattr(self, '_initialized'):
                    self._initialized = True

    @classmethod
    def get_vcenter_configurations(cls):
        """vCenterの設定を取得"""
        return cls._vcenter_configurations

    @classmethod
    def set_vcenter_configurations(cls, configurations):
        """vCenterの設定を設定"""
        with cls._lock:
            cls._vcenter_configurations = configurations 