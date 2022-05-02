"""
Logging functionality
"""

import abc
import logging
import sys

from typing import Dict, List, Optional, Type

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QPlainTextEdit, QWidget


_LOG_PATH = 'stashofexile.log'


class Coloring(abc.ABC):
    """Defines coloring for loggers."""

    console_colors: Dict[int, str]
    reset: str


class ConsoleColoring(Coloring):
    """Coloring for console logging."""

    console_colors = {
        logging.DEBUG: '\x1b[38;20m',
        logging.INFO: '\x1b[38;20m',
        logging.WARNING: '\x1b[33;20m',
        logging.ERROR: '\x1b[31;1m',
        logging.CRITICAL: '\x1b[31;20m',
    }
    reset = '\x1b[0m'


class ApplicationColoring(Coloring):
    """Coloring for application logging."""

    _SPAN = '<span style="color:{}">'
    console_colors = {
        logging.DEBUG: _SPAN.format('white'),
        logging.INFO: _SPAN.format('white'),
        logging.WARNING: _SPAN.format('#e5e510'),
        logging.ERROR: _SPAN.format('#f14c4c'),
        logging.CRITICAL: _SPAN.format('#cd3131'),
    }
    reset = '</span>'


class ColorFormatter(logging.Formatter):
    """Formatter with custom format string and coloring."""

    def __init__(self, fmt: str, coloring: Type[Coloring]):
        super().__init__()
        self.fmt = fmt
        self.coloring = coloring

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = (
            self.coloring.console_colors.get(record.levelno, '')
            + self.fmt
            + self.coloring.reset
        )
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class LogBox(QPlainTextEdit):
    """Log box widget."""

    append_html = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.append_html.connect(self.appendHtml)


class TextEditHandler(logging.Handler):
    """Logger associated with a text edit."""

    def __init__(self):
        super().__init__()
        self.widget: Optional[LogBox] = None
        self.setLevel(logging.WARNING)

    def create_widget(self, parent: Optional[QWidget] = None) -> LogBox:
        """Create associated text edit."""
        self.widget = LogBox(parent)
        self.widget.setReadOnly(True)
        self.widget.setMinimumHeight(300)
        return self.widget

    def set_formatter(self) -> None:
        """Set user readable log format."""
        self.setFormatter(
            ColorFormatter('[%(levelname)s] %(message)s', ApplicationColoring)
        )

    def emit(self, record) -> None:
        msg = self.format(record)
        if self.widget is not None:
            self.widget.append_html.emit(msg)


qlogger = TextEditHandler()


def get_logger(name: str) -> logging.Logger:
    """Creates a formatted logger given a name."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    handlers: List[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(_LOG_PATH, 'a+'),
        qlogger,
    ]

    for handler in handlers:
        handler.setFormatter(
            ColorFormatter(
                '[%(asctime)s %(name)s:%(lineno)d %(levelname)s]\t%(message)s',
                ConsoleColoring,
            )
        )
        logger.addHandler(handler)

    qlogger.set_formatter()

    return logger


def _handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    get_logger(__name__).critical(
        "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
    )


sys.excepthook = _handle_exception
