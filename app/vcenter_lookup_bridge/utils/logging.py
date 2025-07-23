import functools
import logging
import logging.handlers
import os
import pprint
import setuptools


class Logging(object):
    """ロギングクラス"""

    # const
    LOGGER_NAME = "uvicorn.app"
    FUNC_LOGGER_ARGS_LENGTH_MAX_DEFAULT = 20

    @classmethod
    def init(cls, log_dir, log_file):
        log_level = cls.get_loglevel_from_string(os.getenv("VLB_LOG_LEVEL", "INFO"))
        log_path = "{}/{}".format(log_dir, log_file)

        # ログファイルの変更を検出するハンドラの作成
        handler = logging.handlers.WatchedFileHandler(filename=log_path)
        formatter = logging.Formatter(
            '"%(asctime)s.%(msecs)d"\t%(levelname)s\t%(message)s', datefmt="%Y/%m/%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        cls.get_logger().addHandler(handler)

        # アプリケーション共通のログレベルを設定
        cls.get_logger().setLevel(log_level)

    @classmethod
    def get_logger(cls):
        logger = logging.getLogger(cls.LOGGER_NAME)
        return logger

    @classmethod
    def func_logger(cls, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if bool(setuptools.distutils.util.strtobool(os.getenv("VLB_FUNC_LOGGER_ENABLED", "True"))):
                func_name_str = func.__name__
                # class/moduleのメソッドである場合は、クラス/モジュール名も出力する
                if hasattr(func, "__module__"):
                    func_name_str = f"{func.__module__}.{func.__name__}"

                # VLB_FUNC_LOGGER_ARGS_OUTPUTが'True'の場合は、引数を出力する
                if bool(setuptools.distutils.util.strtobool(os.getenv("VLB_FUNC_LOGGER_ARGS_OUTPUT", "False"))):
                    args_dict = cls._args_to_str(args)
                    cls.info(
                        f"FUNC_CALLED / {func_name_str}: start (args_id={id(args)}, args = \n{pprint.pformat(args_dict)})"
                    )
                else:
                    cls.info(f"FUNC_CALLED / {func_name_str}: start (args_id={id(args)})")

                v = func(*args, **kwargs)
                cls.info(f"FUNC_CALLED / {func_name_str}: end (args_id={id(args)})")
                return v
            else:
                return func(*args, **kwargs)

        return wrapper

    @classmethod
    def _args_to_str(cls, args):
        args_dict = {}
        non_dict_index = 0
        for arg in args:
            if hasattr(arg, "__dict__"):
                for key, value in (vars(arg)).items():
                    # フィールド名に__を含む場合は、スキップ
                    if key.startswith("__"):
                        continue
                    # フィールド名がパスワードと思われるキーの場合は、直を*****に置き換える
                    if key.upper() in ["pass"]:
                        value = "*****"
                    # フィールドが呼び出し可能な場合は、スキップ
                    if callable(value):
                        continue
                    # フィールドがメソッドの場合は、スキップ
                    if type(value) in [staticmethod, classmethod]:
                        continue
                    args_dict[key] = cls._truncate_string(
                        target_string=str(value),
                        max_length=int(
                            os.getenv("VLB_FUNC_LOGGER_ARGS_LENGTH_MAX", cls.FUNC_LOGGER_ARGS_LENGTH_MAX_DEFAULT)
                        ),
                    )
            else:
                # フィールドが呼び出し可能な場合は、スキップ
                if callable(arg):
                    continue
                # フィールドがメソッドの場合は、スキップ
                if type(arg) in [staticmethod, classmethod]:
                    continue
                args_dict[str(non_dict_index)] = cls._truncate_string(
                    target_string=str(arg),
                    max_length=int(
                        os.getenv("VLB_FUNC_LOGGER_ARGS_LENGTH_MAX", cls.FUNC_LOGGER_ARGS_LENGTH_MAX_DEFAULT)
                    ),
                )
                non_dict_index += 1
        return args_dict

    @staticmethod
    def _truncate_string(target_string, max_length, trunceted_mark=" ~"):
        if len(target_string) > max_length:
            return target_string[0:max_length] + trunceted_mark
        else:
            return target_string

    @staticmethod
    def get_loglevel_from_string(log_level_string):
        match log_level_string.upper():
            case "DEBUG":
                return logging.DEBUG
            case "INFO":
                return logging.INFO
            case "WARNING":
                return logging.WARNING
            case "ERROR":
                return logging.ERROR
            case "CRITICAL":
                return logging.CRITICAL

    @classmethod
    def info(cls, message):
        cls.get_logger().info(message)

    @classmethod
    def warning(cls, message):
        cls.get_logger().warning(message)

    @classmethod
    def error(cls, message):
        cls.get_logger().error(message)

    @classmethod
    def debug(cls, message):
        cls.get_logger().debug(message)
