import os

from uvicorn.workers import UvicornWorker

# const
WORKER_LOG_CONFIG_FILE_DEFAULT = "./config/uvicorn_config_log.yml"

class MyUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {
        "log_config": os.getenv('VLB_WORKER_LOG_CONFIG_FILE', "./config/uvicorn_config_log.yml"),
    }
