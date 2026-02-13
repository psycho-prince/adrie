"""Centralized logging configuration for the ADRIE application.

Configures Python's standard 'logging' module for structured, production-ready logging.
"""

import json
import logging
import os
from datetime import datetime

from adrie.core.config import settings
from adrie.middleware.request_id import request_id_ctx  # Import ContextVar


class JsonFormatter(logging.Formatter):
    """A custom logging formatter that outputs log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        # Attempt to get request_id from ContextVar
        request_id = request_id_ctx.get(None)

        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
            "pathname": record.pathname,
            "process": record.process,
            "thread": record.thread,
            "app_name": settings.APP_NAME,
            "app_version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }
        if request_id:
            log_record["request_id"] = request_id

        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_record["stack_info"] = self.formatStack(record.stack_info)

        # Add any extra attributes passed to the logger
        for key, value in record.__dict__.items():
            if key not in log_record and not key.startswith("_"):
                log_record[key] = value

        return json.dumps(log_record)


def configure_logging() -> None:
    """Set up the logging configuration for the application.

    - Configures a console handler for human-readable output
      (or simplified JSON in production).
    - Configures a file handler for structured JSON logs.
    """
    # Ensure logs directory exists
    log_dir = (
        os.path.dirname(settings.LOG_FILE_PATH) if settings.LOG_FILE_PATH else "logs"
    )
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)

    # Clear existing handlers to prevent duplicate logs in case of re-configuration
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)

    # Console Handler
    console_handler = logging.StreamHandler()
    if settings.ENVIRONMENT == "production":
        console_handler.setFormatter(JsonFormatter())
    else:
        # More human-readable format for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler for structured JSON logs
    if settings.LOG_FILE_PATH:
        file_handler = logging.FileHandler(settings.LOG_FILE_PATH)
        file_handler.setFormatter(JsonFormatter())
        root_logger.addHandler(file_handler)

    # Suppress verbose loggers from libraries
    logging.getLogger("uvicorn").propagate = False
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


# Call configuration on import
configure_logging()
