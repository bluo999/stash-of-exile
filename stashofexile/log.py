"""
Logging functionality
"""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Creates a formatted logger given a name."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '[%(asctime)s %(name)s:%(lineno)d %(levelname)s]\t%(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
