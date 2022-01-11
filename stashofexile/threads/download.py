"""
Contains image downloading related classes.
"""

import http
import os
import urllib.request
import urllib.error

from typing import Tuple

import log
import util

from threads import thread

# from threads.thread import Ret, RetrieveThread, ThreadManager

logger = log.get_logger(__name__)


class DownloadManager(thread.ThreadManager):
    """Manages downloading images for items."""

    def __init__(self):
        super().__init__(DownloadThread)

    def get_image(self, icon: str, file_path: str) -> Tuple[None]:
        """Gets an image given item info."""
        util.create_directories(file_path)
        if not os.path.exists(file_path):
            logger.debug('Downloading image to %s', file_path)
            # Download image
            try:
                urllib.request.urlretrieve(icon, file_path)
            except urllib.error.HTTPError as e:
                logger.error('HTTP error: %s %s', e.code, e.reason)
                if e.code == http.HTTPStatus.TOO_MANY_REQUESTS:
                    logger.error('%s received, aborting image downloads', e.code)
                    self.too_many_reqs([])
            except urllib.error.URLError as e:
                logger.error('URL error: %s', e.reason)

        return (None,)


class DownloadThread(thread.RetrieveThread):
    """Thread that downloads images."""

    def __init__(self, download_manager: DownloadManager) -> None:
        super().__init__(download_manager)

    def service_success(self, ret: thread.Ret) -> None:
        """Don't do anything for now."""
