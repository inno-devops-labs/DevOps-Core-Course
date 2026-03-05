"""
JSON logging configuration for Loki integration.
Uses python-json-logger for structured log output.
"""

import logging
import sys
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """JSON formatter with timestamp, level, message, and extra fields."""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        if record.name != "root":
            log_record["logger"] = record.name
        # Include extra fields from record (method, path, status_code, client_ip, etc.)
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "message", "asctime",
            ) and value is not None:
                log_record[key] = value


def setup_json_logging():
    """Configure root logger for JSON output."""
    log_handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S.%fZ",
    )
    log_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(log_handler)
    root_logger.setLevel(logging.INFO)

    # Configure uvicorn loggers to use JSON
    for log_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uvicorn_log = logging.getLogger(log_name)
        uvicorn_log.handlers = []
        uvicorn_log.addHandler(log_handler)
