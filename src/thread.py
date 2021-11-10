"""
Threads used in the application.
"""

import os
import re
import urllib.request

from functools import partial
from typing import List
from urllib.error import HTTPError, URLError

from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QStatusBar

import log

from consts import STATUS_TIMEOUT
from item import Item
from util import create_directories


logger = log.get_logger(__name__)


IMAGE_CACHE_DIR = os.path.join('..', 'image_cache')


def _retrieves(items: List[Item]) -> None:
    """Download images for each item."""
    for item in items:
        if item.downloaded:
            continue

        # Extract file path from web url
        if item.file_path == '':
            z = re.search(r'\/([^.]+\.png)', item.icon)
            if z is not None:
                paths = z.group().split('/')
                item.file_path = os.path.join(IMAGE_CACHE_DIR, *paths)

        create_directories(item.file_path)
        if not os.path.exists(item.file_path):
            logger.debug('Downloading image to %s', item.file_path)
            # Download image
            try:
                urllib.request.urlretrieve(item.icon, item.file_path)
            except HTTPError as e:
                logger.error('HTTP error: %s %s', e.code, e.reason)
            except URLError as e:
                logger.error('URL error: %s', e.reason)

        item.downloaded = True


def _download_finished(statusbar: QStatusBar) -> None:
    """Shows a status message, when the download thread finishes."""
    statusbar.showMessage('Image downloading finished', STATUS_TIMEOUT)


class DownloadThread(QThread):
    """Thread that downloads images for each item."""

    def __init__(self, statusbar: QStatusBar, items: List[Item]) -> None:
        QThread.__init__(self, statusbar)
        self.items = items
        self.finished.connect(partial(_download_finished, statusbar))

    def run(self) -> None:
        """Runs the thread."""
        _retrieves(self.items)
