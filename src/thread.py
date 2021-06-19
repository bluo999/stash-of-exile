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


def _retrieves(items: List[Item]):
    for item in items:
        if item.downloaded:
            continue

        if item.filePath == '':
            searchObj = re.search(r'\/([^.]+\.png)', item.icon)
            item.filePath = f'../cache{searchObj.group()}'
        filePath = item.filePath

        directory = os.path.dirname(filePath)
        if not os.path.exists(filePath):
            print('Downloading image to', filePath)
            pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(item.icon, item.filePath)
        item.downloaded = True


def _download_finished(statusbar: QStatusBar):
    statusbar.showMessage('Image downloading finished', STATUS_TIMEOUT)


class DownloadThread(QThread):
    def __init__(
        self, tooltipImage: QTextEdit, statusbar: QStatusBar, items: List[Item]
    ):
        super(DownloadThread, self).__init__(tooltipImage)
        self.items = items
        self.finished.connect(partial(_download_finished, statusbar))

    def run(self):
        _retrieves(self.items)
