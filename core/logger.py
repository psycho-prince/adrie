"""Centralized logging utility for the ADRIE application.

Provides a pre-configured logger instance that uses the settings defined in configs/logging_config.py.
"""

import logging

from core.logging import (
    configure_logging,
)  # Import to ensure logging is configured

# Ensure logging is configured when this module is imported
configure_logging()


def get_logger(name: str = __name__) -> logging.Logger:
    """Return a configured logger instance.

    Args:
        name (str): The name of the logger. Defaults to the current module's name.

    Returns:
        logging.Logger: A logger instance with ADRIE's configuration.

    """
    return logging.getLogger(name)


# Example usage:
# from app.core.logger import get_logger
# logger = get_logger(__name__)
# logger.info("This is an info message from the core logger.")
