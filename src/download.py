"""
Contains image downloading related classes.
"""

import os
import re
import urllib.request

from http import HTTPStatus
from typing import List
from urllib.error import HTTPError, URLError

import log
import util

from item import Item
from thread import IMAGE_CACHE_DIR

logger = log.get_logger(__name__)


def _retrieves(items: List[Item]) -> None:
    """Downloads images for each item."""
    for item in items:
        # Extract file path from web url
        if item.file_path == '':
            z = re.search(r'\/([^.]+\.png)', item.icon)
            if z is not None:
                paths = z.group().split('/')
                item.file_path = os.path.join(IMAGE_CACHE_DIR, *paths)

        util.create_directories(item.file_path)
        if not os.path.exists(item.file_path):
            logger.debug('Downloading image to %s', item.file_path)
            # Download image
            try:
                urllib.request.urlretrieve(item.icon, item.file_path)
            except HTTPError as e:
                logger.error('HTTP error: %s %s', e.code, e.reason)
                if e.code == HTTPStatus.TOO_MANY_REQUESTS:
                    logger.error('%s received, aborting image downloads', e.code)
                    break
            except URLError as e:
                logger.error('URL error: %s', e.reason)


# def _download_finished(statusbar: QStatusBar) -> None:
#     """Shows a status message, when the download thread finishes."""
#     statusbar.showMessage('Image downloading finished', STATUS_TIMEOUT)


# class DownloadThread(QThread):
#     """Thread that downloads images for each item."""

#     def __init__(self, items: List[Item]) -> None:
#         QThread.__init__(self)
#         self.items = items
#         # self.finished.connect(partial(_download_finished, statusbar))

#     def run(self) -> None:
#         """Runs the thread."""
#         _retrieves(self.items)
