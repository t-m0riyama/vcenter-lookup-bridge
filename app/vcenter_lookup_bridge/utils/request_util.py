import uuid

__version__ = "1.0"


class RequestUtil(object):
    """HTTPリクエストを支援するヘルパークラス"""

    @classmethod
    def get_request_id(cls):
        return str(uuid.uuid4())
