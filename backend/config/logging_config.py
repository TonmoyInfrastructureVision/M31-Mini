import os
import logging
import logging.config
from typing import Dict, Any
import json
from datetime import datetime
import sys

from pythonjsonlogger import jsonlogger
from config.settings import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["environment"] = settings.environment
        log_record["service"] = "m31-mini-backend"
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name


def setup_logging() -> Dict[str, Any]:
    log_dir = os.path.dirname(settings.logging.file or "./logs/m31_mini.log")
    os.makedirs(log_dir, exist_ok=True)
    
    log_format = settings.logging.format
    date_format = settings.logging.date_format
    
    handlers = ["console"]
    if settings.logging.file:
        handlers.append("file")
        
    if settings.logging.json_logs:
        handlers.append("json")
        
    if settings.logging.logstash_enabled and settings.logging.logstash_host:
        handlers.append("logstash")
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": log_format,
                "datefmt": date_format,
            },
            "json": {
                "()": CustomJsonFormatter,
                "format": "%(timestamp)s %(level)s %(name)s %(message)s",
                "datefmt": date_format,
            },
        },
        "handlers": {
            "console": {
                "level": settings.logging.level,
                "class": "logging.StreamHandler",
                "formatter": "standard" if not settings.logging.json_logs else "json",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "": {
                "handlers": handlers,
                "level": settings.logging.level,
                "propagate": True,
            },
            "uvicorn": {
                "handlers": handlers,
                "level": settings.logging.level,
                "propagate": False,
            },
            "fastapi": {
                "handlers": handlers,
                "level": settings.logging.level,
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": handlers,
                "level": "WARNING",
                "propagate": False,
            },
            "celery": {
                "handlers": handlers,
                "level": settings.logging.level,
                "propagate": False,
            },
        },
    }
    
    # Add file handler if enabled
    if settings.logging.file:
        config["handlers"]["file"] = {
            "level": settings.logging.level,
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard" if not settings.logging.json_logs else "json",
            "filename": settings.logging.file,
            "maxBytes": settings.logging.max_size_mb * 1024 * 1024,
            "backupCount": settings.logging.backup_count,
        }
    
    # Add logstash handler if enabled
    if settings.logging.logstash_enabled and settings.logging.logstash_host:
        try:
            import logstash
            
            config["handlers"]["logstash"] = {
                "level": settings.logging.level,
                "class": "logstash.LogstashHandler",
                "host": settings.logging.logstash_host,
                "port": settings.logging.logstash_port or 5959,
                "version": 1,
                "message_type": "m31-mini-logs",
                "tags": ["m31-mini", settings.environment],
            }
        except ImportError:
            print("Logstash handler requested but python-logstash not installed")
    
    return config


def configure_logging() -> None:
    config = setup_logging()
    logging.config.dictConfig(config)
    

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name) 