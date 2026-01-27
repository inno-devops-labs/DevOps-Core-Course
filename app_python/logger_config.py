import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"}
    },
    "handlers": {
        "console": {
            "class": logging.StreamHandler,
            "formatter": "default",
            "level": "INFO",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}


def setup_logger() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)
