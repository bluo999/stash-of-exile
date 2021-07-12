import os
import pathlib
import re
import urllib.request

from functools import partial
from typing import List

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QTextEdit, QStatusBar

from consts import STATUS_TIMEOUT
from item import Item


def _retrieves(items: List[Item]) -> None:
    """Download images for each item."""
    for item in items:
        if item.downloaded:
            continue

        # Extract filePath from web url
        if item.filePath == '':
            searchObj = re.search(r'\/([^.]+\.png)', item.icon)
            if searchObj is not None:
                item.filePath = f'../cache{searchObj.group()}'

        directory = os.path.dirname(item.filePath)
        if not os.path.exists(item.filePath):
            print('Downloading image to', item.filePath)
            # Create directories
            pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
            # Download image
            urllib.request.urlretrieve(item.icon, item.filePath)
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
        _retrieves(self.items)
