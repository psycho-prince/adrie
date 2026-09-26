"""Logging config — fixed: URL objects are not JSON-safe; serialize to string."""
import json, logging, os
from datetime import datetime
from core.config import settings
from core.request_id_ctx import request_id_ctx

class JsonFormatter(logging.Formatter):
    def format(self, record):
        request_id = request_id_ctx.get(None)
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
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
        # Only serialize primitives; skip non-JSON-safe extras (e.g. httpx URL objects)
        for key, value in record.__dict__.items():
            if key not in log_record and not key.startswith("_"):
                try:
                    json.dumps(value)
                    log_record[key] = value
                except (TypeError, ValueError):
                    log_record[key] = repr(value)
        return json.dumps(log_record)

def configure_logging():
    log_dir = os.path.dirname(settings.LOG_FILE_PATH) if settings.LOG_FILE_PATH else "logs"
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL)
    if root.handlers:
        for h in root.handlers:
            root.removeHandler(h)
    console = logging.StreamHandler()
    if settings.ENVIRONMENT == "production":
        console.setFormatter(JsonFormatter())
    else:
        console.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    root.addHandler(console)
    if settings.LOG_FILE_PATH:
        fh = logging.FileHandler(settings.LOG_FILE_PATH)
        fh.setFormatter(JsonFormatter())
        root.addHandler(fh)
    logging.getLogger("uvicorn").propagate = False
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    # Suppress httpx2 noisy access logging during tests
    logging.getLogger("httpx2").setLevel(logging.WARNING)

configure_logging()
