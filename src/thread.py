"""
Threads used in the application.
"""

import os
import re
import urllib.request

from functools import partial
from typing import List
from urllib.error import HTTPError, URLError

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QStatusBar

from apimanager import APIManager
from consts import STATUS_TIMEOUT
from item import Item
from util import create_directories


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
                item.file_path = IMAGE_CACHE_DIR + z.group()

        create_directories(item.file_path)
        if not os.path.exists(item.file_path):
            print('Downloading image to', item.file_path)
            # Download image
            try:
                urllib.request.urlretrieve(item.icon, item.file_path)
            except HTTPError as e:
                print('HTTP error:', e.code)
            except URLError as e:
                print('URL error:', e.reason)

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


class APIThread(QThread):
    """Thread that handles API calls."""

    output = pyqtSignal(object, object, object)

    def __init__(self, api_manager: APIManager) -> None:
        QThread.__init__(self)
        self.api_manager = api_manager

    def run(self) -> None:
        """Runs the thread."""
        while True:
            ret = self.api_manager.consume()
            if ret is None:
                break

            cb_obj, cb, args = ret
            self.output.emit(cb_obj, cb, args)
