"""Project wide logging configuration"""

import logging.config

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(levelname)s %(asctime)s %(module)s %(message)s",
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "standard",
        }
    },
    "loggers": {
        "root": {"handlers": ["stdout"], "level": "INFO"},
        "api": {"handlers": ["stdout"], "level": "INFO"},
        "tgbot": {"handlers": ["stdout"], "level": "INFO"},
        "alertmanager_workers": {"handlers": ["stdout"], "level": "INFO"},
        "chatbot": {"handlers": ["stdout"], "level": "INFO"}
    },
}

logging.config.dictConfig(LOGGING)

root_logger = logging.getLogger("root")

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('telethon').setLevel(logging.CRITICAL)
