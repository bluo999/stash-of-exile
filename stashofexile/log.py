"""
Logging functionality
"""

import logging
import os
import sys

from typing import List

_LOG_PATH = os.path.join('..', 'stashofexile.log')


def get_logger(name: str) -> logging.Logger:
    """Creates a formatted logger given a name."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '[%(asctime)s %(name)s:%(lineno)d %(levelname)s]\t%(message)s'
    )
    handlers: List[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(_LOG_PATH, 'a+'),
    ]

    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


error_logger = get_logger(__name__)


def _handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_logger.critical(
        "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
    )


sys.excepthook = _handle_exception
