"""Logger helper — imports from local core.logging."""
import logging
from .logging import configure_logging

configure_logging()

def get_logger(name: str = __name__) -> logging.Logger:
    return logging.getLogger(name)
