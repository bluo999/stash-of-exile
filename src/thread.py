"""
Threads used in the application.
"""

import os
import pathlib
import re
import urllib.request

from functools import partial
from typing import List
from urllib.error import HTTPError, URLError

from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QStatusBar

from consts import STATUS_TIMEOUT
from item import Item


def _retrieves(items: List[Item]) -> None:
    """Download images for each item."""
    for item in items:
        if item.downloaded:
            continue

        # Extract filePath from web url
        if item.file_path == '':
            z = re.search(r'\/([^.]+\.png)', item.icon)
            if z is not None:
                item.file_path = f'../cache{z.group()}'

        directory = os.path.dirname(item.file_path)
        if not os.path.exists(item.file_path):
            print('Downloading image to', item.file_path)
            # Create directories
            pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
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
