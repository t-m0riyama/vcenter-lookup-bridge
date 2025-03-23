import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# アプリケーションのルートディレクトリをPythonパスに追加
app_root = str(Path(__file__).parent.parent)
sys.path.insert(0, app_root)

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from main import app
from vcenter_lookup_bridge.vmware.vcenter_config_manager import VCenterConfigManager


@pytest.fixture(autouse=True)
def setup_test_env():
    """テスト環境のセットアップ"""
    # 環境変数の設定
    os.environ["TESTING"] = "1"
    os.environ["VLB_CACHE_HOSTNAME"] = "localhost"
    os.environ["VLB_CACHE_PORT"] = "6379"
    os.environ["VLB_CACHE_EXPIRE_SECS"] = "300"
    os.environ["VLB_LOG_DIR"] = "/tmp/vlb_test_logs"
    os.environ["VLB_LOG_FILE"] = "vlb_test.log"
    os.environ["VLB_LOG_LEVEL"] = "DEBUG"

    # ログディレクトリの作成
    log_dir = Path(os.environ["VLB_LOG_DIR"])
    log_dir.mkdir(parents=True, exist_ok=True)

    # FastAPICache初期化
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")

    # テスト用のvCenter設定
    test_config = {
        "test-vcenter": {
            "hostname": "test-vcenter.example.com",
            "username": "test-user",
            "password": "test-password",
            "port": 443,
            "disable_ssl_verification": True,
            "ignore_ssl_cert_verify": True,
            "proxy_host": None,
            "proxy_port": None
        }
    }
    VCenterConfigManager.set_vcenter_configurations(test_config)
    yield

    # テストログファイルの削除
    log_file = log_dir / os.environ["VLB_LOG_FILE"]
    if log_file.exists():
        log_file.unlink()

    # テスト後にvCenter設定をクリア
    VCenterConfigManager.set_vcenter_configurations({})

@pytest.fixture
def test_client():
    """テストクライアントを作成"""
    return TestClient(app)
