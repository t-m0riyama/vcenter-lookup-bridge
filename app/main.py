import os
import pathlib
import sys
from contextlib import asynccontextmanager

import uvicorn
import vcenter_lookup_bridge.vmware.instances as g
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from vcenter_lookup_bridge.api.main import api_router
from vcenter_lookup_bridge.utils.config_util import ConfigUtil
from vcenter_lookup_bridge.utils.constants import Constants as cs
from vcenter_lookup_bridge.utils.logging import Logging
from vcenter_lookup_bridge.vmware.connector import Connector

# const
LOG_DIR_DEFAULT = "./log"
LOG_FILE_DEFAULT = "vcenter_lookup_bridge.log"
CONFIG_DIR_DEFAULT = "./config"
CONFIG_VCENTER_DIR_DEFAULT = "./config/vcenters"
VLB_ADDRESS_DEFAULT = "0.0.0.0"
VLB_PORT_DEFAULT = 8000
VLB_CACHE_HOSTNAME_DEFAULT = "cache"
VLB_CACHE_PORT_DEFAULT = 6379


g.vcenter_configurations = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    Logging.info("Initializing.")
    cache_host = os.getenv("VLB_CACHE_HOSTNAME", VLB_CACHE_HOSTNAME_DEFAULT)
    cache_port = int(os.getenv("VLB_CACHE_PORT", VLB_CACHE_PORT_DEFAULT))

    # Load Configss
    try:
        for vcenter_config in pathlib.Path(f'{CONFIG_VCENTER_DIR_DEFAULT}').iterdir():
            if vcenter_config.suffix == ".yml":
                config = ConfigUtil.parse_config(f'{vcenter_config}')
                g.vcenter_configurations[config["name"]] = config
    except Exception as e:
        Logging.error(
            f"vCneterの設定ファイルを読み込めませんでした(STATUS/{cs.EXIT_ERR_LOAD_CONFIG})"
        )
        Logging.error(e)
        sys.exit(cs.EXIT_ERR_LOAD_CONFIG)

    # Initialize Cache
    redis = aioredis.from_url(f"redis://{cache_host}:{cache_port}")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    Logging.info(redis)

    Connector.get_service_instances(
        configs=g.vcenter_configurations,
    )
    Logging.info("Startup completed.")
    yield
    await redis.close()
    Logging.info("Shutdown completed.")

app = FastAPI(
    title='vCenter Lookup Bridge API',
    summary='vCenterに接続し、仮想マシン・データストア・ポートグループなどの情報を参照するAPIです。',
    description='vCenter Lookup Bridge API',
    version='0.1.0',
    lifespan=lifespan,
    root_path='/vcenter-lookup-bridge',
    openapi_url='/api/v1/openapi.json',
    docs_url='/api/v1/docs',
)
app.include_router(api_router, prefix='/api/v1')

# Initialize Logging
log_dir = os.getenv("VLB_LOG_DIR", LOG_DIR_DEFAULT)
log_file = os.getenv("VLB_LOG_FILE", LOG_FILE_DEFAULT)
Logging.init(log_dir, log_file)

if __name__ == '__main__':
    # gunicorn、uvicornコマンドで実行する場合、以下設定は無視されます。
    listen_address = os.getenv("VLB_LISTEN_ADDRESS", VLB_ADDRESS_DEFAULT)
    listen_port = os.getenv("VLB_PORT", VLB_PORT_DEFAULT)
    uvicorn.run(app, host=listen_address, port=listen_port)
