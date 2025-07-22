import os
from typing import Dict, Optional, Literal
from redis import asyncio as aioredis
from redis import Redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError
import re


class VCenterWSSessionError(Exception):
    """vCenter接続管理に関する例外"""

    pass


class VCenterWSSessionManager:
    """vCenterのWeb Serivice APIのセッション状態を管理するクラス

    このクラスは、Redisを使用してvCenterのセッションの状態を管理します。
    各vCenterの接続状態は、キーと値のペアとしてRedisに保存され、
    一定時間後に自動的に削除されます。

    Attributes:
        VLB_CACHE_HOSTNAME_DEFAULT (str): Redisサーバーのデフォルトホスト名
        VLB_CACHE_PORT_DEFAULT (int): Redisサーバーのデフォルトポート番号
        VCENTER_WS_SESSION_PREFIX (str): vCenter接続状態のキープレフィックス
        VCENTER_WS_SESSION_EXPIRE_SEC (int): 接続状態のデフォルト有効期限（秒）
        VCENTER_STATUS_ALIVE (str): 接続状態が正常であることを示す値
        VCENTER_STATUS_DEAD (str): 接続状態が異常であることを示す値
        VCENTER_NAME_PATTERN (str): vCenter名の正規表現パターン
        REDIS_TIMEOUT (int): Redis接続のタイムアウト時間（秒）

    Note:
        名前が_asyncで終わるメソッドは非同期（async）で実装されており、
        呼び出し側で適切にawaitする必要があります。
    """

    # 定数定義
    VLB_CACHE_HOSTNAME_DEFAULT = "cache"
    VLB_CACHE_PORT_DEFAULT = 6379
    VCENTER_WS_SESSION_PREFIX = "vlb_vcenter_ws_session:"
    VCENTER_WS_SESSION_EXPIRE_SEC = 120
    VCENTER_STATUS_ALIVE = "alive"
    VCENTER_STATUS_DEAD = "dead"
    VCENTER_NAME_PATTERN = r"^[a-zA-Z0-9_-]+$"
    REDIS_TIMEOUT = 5

    # 型定義
    VCenterStatus = Literal["alive", "dead"]

    @staticmethod
    def validate_vcenter_name(vcenter_name: str) -> None:
        """
        vCenter名の形式を検証します

        Args:
            vcenter_name: 検証するvCenter名

        Raises:
            VCenterWSSessionError: vCenter名が不正な場合
        """
        if not vcenter_name or not isinstance(vcenter_name, str):
            raise VCenterWSSessionError("vCenter名は空文字列またはNoneにできません")
        if not re.match(VCenterWSSessionManager.VCENTER_NAME_PATTERN, vcenter_name):
            raise VCenterWSSessionError("vCenter名は英数字、アンダースコア、ハイフンのみ使用可能です")

    @staticmethod
    def initialize() -> Redis:
        """
        Redis接続を初期化します

        Returns:
            Redis: 初期化されたRedis接続オブジェクト

        Raises:
            VCenterWSSessionError: Redis接続に失敗した場合
        """
        try:
            cache_host = os.getenv(
                "VLB_CACHE_HOSTNAME",
                VCenterWSSessionManager.VLB_CACHE_HOSTNAME_DEFAULT,
            )
            cache_port = int(os.getenv("VLB_CACHE_PORT", VCenterWSSessionManager.VLB_CACHE_PORT_DEFAULT))
            redis = Redis.from_url(
                f"redis://{cache_host}:{cache_port}",
                socket_timeout=VCenterWSSessionManager.REDIS_TIMEOUT,
                socket_connect_timeout=VCenterWSSessionManager.REDIS_TIMEOUT,
            )
            return redis
        except (RedisError, ValueError, TypeError) as e:
            raise VCenterWSSessionError(f"Redis接続の初期化に失敗しました: {str(e)}")

    @staticmethod
    async def initialize_async() -> Redis:
        """
        Redis接続を初期化します

        Returns:
            Redis: 初期化されたRedis接続オブジェクト

        Raises:
            VCenterWSSessionError: Redis接続に失敗した場合
        """
        try:
            cache_host = os.getenv(
                "VLB_CACHE_HOSTNAME",
                VCenterWSSessionManager.VLB_CACHE_HOSTNAME_DEFAULT,
            )
            cache_port = int(os.getenv("VLB_CACHE_PORT", VCenterWSSessionManager.VLB_CACHE_PORT_DEFAULT))
            redis = aioredis.from_url(
                f"redis://{cache_host}:{cache_port}",
                socket_timeout=VCenterWSSessionManager.REDIS_TIMEOUT,
                socket_connect_timeout=VCenterWSSessionManager.REDIS_TIMEOUT,
            )
            await redis.ping()
            return redis
        except (RedisError, ValueError, TypeError) as e:
            raise VCenterWSSessionError(f"Redis接続の初期化に失敗しました: {str(e)}")

    @staticmethod
    def set_vcenter_ws_session(
        redis: Redis,
        vcenter_name: str,
        status: VCenterStatus = VCENTER_STATUS_ALIVE,
        not_exist: bool = False,
        expire_seconds: int = VCENTER_WS_SESSION_EXPIRE_SEC,
    ) -> None:
        """
        vCenterの接続状態を登録します

        Args:
            redis: Redis接続オブジェクト
            vcenter_name: vCenterの名前
            status: 接続状態（"alive"または"dead"）
            not_exist: 指定したvCenterの名前が未登録の場合のみ、登録する（True）。登録状況に関わらず、登録する（False）
            expire_seconds: 有効期限（秒）

        Raises:
            VCenterWSSessionError: Redis操作に失敗した場合、またはvCenter名が不正な場合
        """
        try:
            VCenterWSSessionManager.validate_vcenter_name(vcenter_name)
            key = f"{VCenterWSSessionManager.VCENTER_WS_SESSION_PREFIX}{vcenter_name}"
            redis.set(key, status, nx=not_exist, ex=expire_seconds)
        except (RedisError, ConnectionError, TimeoutError) as e:
            raise VCenterWSSessionError(f"vCenter接続状態の登録に失敗しました: {str(e)}")

    @staticmethod
    async def set_vcenter_ws_session_async(
        redis: Redis,
        vcenter_name: str,
        status: VCenterStatus = VCENTER_STATUS_ALIVE,
        not_exist: bool = False,
        expire_seconds: int = VCENTER_WS_SESSION_EXPIRE_SEC,
    ) -> None:
        """
        vCenterの接続状態を登録します

        Args:
            redis: Redis接続オブジェクト
            vcenter_name: vCenterの名前
            status: 接続状態（"alive"または"dead"）
            not_exist: 指定したvCenterの名前が未登録の場合のみ、登録する（True）。登録状況に関わらず、登録する（False）
            expire_seconds: 有効期限（秒）

        Raises:
            VCenterWSSessionError: Redis操作に失敗した場合、またはvCenter名が不正な場合
        """
        try:
            VCenterWSSessionManager.validate_vcenter_name(vcenter_name)
            key = f"{VCenterWSSessionManager.VCENTER_WS_SESSION_PREFIX}{vcenter_name}"
            await redis.set(key, status, nx=not_exist, ex=expire_seconds)
        except (RedisError, ConnectionError, TimeoutError) as e:
            raise VCenterWSSessionError(f"vCenter接続状態の登録に失敗しました: {str(e)}")

    @staticmethod
    def get_vcenter_ws_session(redis: Redis, vcenter_name: str) -> Optional[VCenterStatus]:
        """
        vCenterの接続状態を取得します

        Args:
            redis: Redis接続オブジェクト
            vcenter_name: vCenterの名前

        Returns:
            Optional[VCenterStatus]: 接続状態。存在しない場合はNone

        Raises:
            VCenterWSSessionError: Redis操作に失敗した場合、またはvCenter名が不正な場合
        """
        try:
            VCenterWSSessionManager.validate_vcenter_name(vcenter_name)
            result = redis.get(f"{VCenterWSSessionManager.VCENTER_WS_SESSION_PREFIX}{vcenter_name}")
            return result.decode("utf-8") if result else None
        except (RedisError, ConnectionError, TimeoutError) as e:
            raise VCenterWSSessionError(f"vCenter接続状態の取得に失敗しました: {str(e)}")

    @staticmethod
    async def get_vcenter_ws_session_async(redis: Redis, vcenter_name: str) -> Optional[VCenterStatus]:
        """
        vCenterの接続状態を取得します

        Args:
            redis: Redis接続オブジェクト
            vcenter_name: vCenterの名前

        Returns:
            Optional[VCenterStatus]: 接続状態。存在しない場合はNone

        Raises:
            VCenterWSSessionError: Redis操作に失敗した場合、またはvCenter名が不正な場合
        """
        try:
            VCenterWSSessionManager.validate_vcenter_name(vcenter_name)
            result = await redis.get(f"{VCenterWSSessionManager.VCENTER_WS_SESSION_PREFIX}{vcenter_name}")
            return result.decode("utf-8") if result else None
        except (RedisError, ConnectionError, TimeoutError) as e:
            raise VCenterWSSessionError(f"vCenter接続状態の取得に失敗しました: {str(e)}")

    @staticmethod
    def get_all_vcenter_ws_session_informations(
        redis: Redis = None,
    ) -> Dict[str, VCenterStatus]:
        """
        全てのvCenter接続状態を取得します

        Args:
            redis: Redis接続オブジェクト

        Returns:
            Dict[str, VCenterStatus]: vCenter名と接続状態の辞書

        Raises:
            VCenterWSSessionError: Redis操作に失敗した場合
        """
        try:
            if redis is None:
                redis = VCenterWSSessionManager.initialize()
            vcenter_keys = redis.keys(f"{VCenterWSSessionManager.VCENTER_WS_SESSION_PREFIX}*")
            vcenter_ws_sessions = {}
            for vcenter_key in vcenter_keys:
                try:
                    vcenter_name = vcenter_key.decode("utf-8").split(":")[1]
                    status = redis.get(vcenter_key)
                    if status:
                        vcenter_ws_sessions[vcenter_name] = status.decode("utf-8")
                except (IndexError, UnicodeDecodeError):
                    continue
            return vcenter_ws_sessions
        except (RedisError, ConnectionError, TimeoutError) as e:
            raise VCenterWSSessionError(f"vCenter接続状態の一括取得に失敗しました: {str(e)}")

    @staticmethod
    async def get_all_vcenter_ws_session_informations_async(
        redis: Redis,
    ) -> Dict[str, VCenterStatus]:
        """
        全てのvCenter接続状態を取得します

        Args:
            redis: Redis接続オブジェクト

        Returns:
            Dict[str, VCenterStatus]: vCenter名と接続状態の辞書

        Raises:
            VCenterWSSessionError: Redis操作に失敗した場合
        """
        try:
            vcenter_keys = await redis.keys(f"{VCenterWSSessionManager.VCENTER_WS_SESSION_PREFIX}*")
            vcenter_ws_sessions = {}
            for vcenter_key in vcenter_keys:
                try:
                    vcenter_name = vcenter_key.decode("utf-8").split(":")[1]
                    status = await redis.get(vcenter_key)
                    if status:
                        vcenter_ws_sessions[vcenter_name] = status.decode("utf-8")
                except (IndexError, UnicodeDecodeError):
                    continue
            return vcenter_ws_sessions
        except (RedisError, ConnectionError, TimeoutError) as e:
            raise VCenterWSSessionError(f"vCenter接続状態の一括取得に失敗しました: {str(e)}")

    @staticmethod
    def get_or_create_vcenter_ws_session(
        redis: Redis, vcenter_name: str, status: VCenterStatus = VCENTER_STATUS_ALIVE
    ) -> VCenterStatus:
        """
        キーが存在しない場合は新しいキーを登録し、存在する場合はその値を返します

        Args:
            redis: Redis接続オブジェクト
            vcenter_name: vCenterの名前
            status: 接続状態（"alive"または"dead"）

        Returns:
            VCenterStatus: 取得した値または新しく登録した値

        Raises:
            VCenterWSSessionError: Redis操作に失敗した場合、またはvCenter名が不正な場合
        """
        try:
            VCenterWSSessionManager.validate_vcenter_name(vcenter_name)
            status_current = VCenterWSSessionManager.get_vcenter_ws_session(redis, vcenter_name)
            if status_current is None:
                VCenterWSSessionManager.set_vcenter_ws_session(redis, vcenter_name, status)
                status_updated = VCenterWSSessionManager.get_vcenter_ws_session(redis, vcenter_name)
                return status_updated
            return status_current
        except (RedisError, ConnectionError, TimeoutError) as e:
            raise VCenterWSSessionError(f"vCenter接続状態の取得または作成に失敗しました: {str(e)}")

    @staticmethod
    async def get_or_create_vcenter_ws_session_async(
        redis: Redis, vcenter_name: str, status: VCenterStatus = VCENTER_STATUS_ALIVE
    ) -> VCenterStatus:
        """
        キーが存在しない場合は新しいキーを登録し、存在する場合はその値を返します

        Args:
            redis: Redis接続オブジェクト
            vcenter_name: vCenterの名前
            status: 接続状態（"alive"または"dead"）

        Returns:
            VCenterStatus: 取得した値または新しく登録した値

        Raises:
            VCenterWSSessionError: Redis操作に失敗した場合、またはvCenter名が不正な場合
        """
        try:
            VCenterWSSessionManager.validate_vcenter_name(vcenter_name)
            status_current = await VCenterWSSessionManager.get_vcenter_ws_session_async(redis, vcenter_name)
            if status_current is None:
                await VCenterWSSessionManager.set_vcenter_ws_session_async(redis, vcenter_name, status)
                status_updated = await VCenterWSSessionManager.get_vcenter_ws_session_async(redis, vcenter_name)
                return status_updated
            return status_current
        except (RedisError, ConnectionError, TimeoutError) as e:
            raise VCenterWSSessionError(f"vCenter接続状態の取得または作成に失敗しました: {str(e)}")

    @staticmethod
    async def is_dead_vcenter_ws_session_async(redis: Redis, vcenter_name: str) -> bool:
        """
        指定されたvCenterの接続状態がダウンしているかどうかを確認します

        Args:
            redis: Redis接続オブジェクト
            vcenter_name: 確認対象のvCenter名

        Returns:
            bool: vCenterの接続状態が"dead"の場合はTrue、それ以外（"alive"または未登録）の場合はFalse

        Raises:
            VCenterWSSessionError: Redis操作に失敗した場合、またはvCenter名が不正な場合
        """
        try:
            VCenterWSSessionManager.validate_vcenter_name(vcenter_name)
            status = await VCenterWSSessionManager.get_vcenter_ws_session_async(redis, vcenter_name)
            return status == VCenterWSSessionManager.VCENTER_STATUS_DEAD
        except (RedisError, ConnectionError, TimeoutError) as e:
            raise VCenterWSSessionError(f"vCenter接続状態の確認に失敗しました: {str(e)}")

    @staticmethod
    def is_dead_vcenter_ws_session(redis: Redis, vcenter_name: str) -> bool:
        """
        指定されたvCenterの接続状態がダウンしているかどうかを確認します

        Args:
            redis: Redis接続オブジェクト
            vcenter_name: 確認対象のvCenter名

        Returns:
            bool: vCenterの接続状態が"dead"の場合はTrue、それ以外（"alive"または未登録）の場合はFalse

        Raises:
            VCenterWSSessionError: Redis操作に失敗した場合、またはvCenter名が不正な場合
        """
        try:
            VCenterWSSessionManager.validate_vcenter_name(vcenter_name)
            status = VCenterWSSessionManager.get_vcenter_ws_session(redis, vcenter_name)
            return status == VCenterWSSessionManager.VCENTER_STATUS_DEAD
        except (RedisError, ConnectionError, TimeoutError) as e:
            raise VCenterWSSessionError(f"vCenter接続状態の確認に失敗しました: {str(e)}")
