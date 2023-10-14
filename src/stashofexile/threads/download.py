"""
Contains image downloading related classes.
"""

import http
import os
import urllib.error
import urllib.request
from typing import Tuple

from stashofexile import file, log
from stashofexile.threads import thread
from stashofexile.threads.api import HEADERS

logger = log.get_logger(__name__)


class DownloadThread(thread.RetrieveThread):
    """Downloads images for items."""

    def get_image(self, icon: str, file_path: str) -> Tuple[None]:
        """Gets an image given item info."""
        file.create_directories(file_path)
        if not os.path.exists(file_path):
            logger.debug('Downloading image to %s', file_path)
            # Download image
            try:
                request = urllib.request.Request(icon, headers=HEADERS)
                with urllib.request.urlopen(request) as response:
                    output = response.read()
                    with open(file_path, 'wb') as f:
                        f.write(output)
            except urllib.error.HTTPError as e:
                logger.error(
                    'HTTP error: %s %s when downloading %s', e.code, e.reason, icon
                )
                if e.code == http.HTTPStatus.TOO_MANY_REQUESTS:
                    logger.error('%s received, aborting image downloads', e.code)
                    self.too_many_reqs([])
            except urllib.error.URLError as e:
                logger.error('URL error: %s', e.reason)

        return (None,)

    def service_success(self, ret: thread.Ret) -> None:
        """Don't do anything for now."""

    def rate_limit(self, message: str) -> None:
        """There is no rate limiter for this thread."""
