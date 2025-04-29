import logging
import sys
from typing import Dict, Any

from .settings import settings


def setup_logging() -> Dict[str, Any]:
    log_level = getattr(logging, settings.log_level.upper())
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "default",
                "level": log_level,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "m31_mini.log",
                "maxBytes": 10485760,  # 10 MB
                "backupCount": 5,
                "formatter": "default",
                "level": log_level,
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": log_level,
            },
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "celery": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
        },
    }
    
    return logging_config


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    return logger 