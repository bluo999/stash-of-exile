"""
Contains API related classes.
"""

import json
import urllib.request

from functools import wraps
from http import HTTPStatus
from typing import Any, List
from urllib.error import HTTPError, URLError

from PyQt6.QtCore import pyqtSignal

import log

from ratelimiting import RateLimit, RateLimiter
from thread import Ret, RetrieveThread, ThreadManager

logger = log.get_logger(__name__)

# HTTPS request headers
HEADERS = {'User-Agent': 'stash-of-exile/0.1.0 (contact:brianluo999@gmail.com)'}

URL_LEAGUES = 'https://api.pathofexile.com/leagues?type=main&compact=1'
URL_TAB_INFO = (
    'https://pathofexile.com/character-window/get-stash-items'
    + '?accountName={}&league={}&tabs=1'
)
URL_TAB_ITEMS = URL_TAB_INFO + '&tabIndex={}'
URL_CHARACTERS = 'https://pathofexile.com/character-window/get-characters'
URL_CHAR_ITEMS = (
    'https://pathofexile.com/character-window/get-items?accountName={}&character={}'
)


# Default rate limit values (hits, period (in ms))
RATE_LIMITS = [RateLimit(45, 60000), RateLimit(240, 240000)]


def _elevated_request(url: str, poesessid: str) -> urllib.request.Request:
    """Wraps a request that requires POESESSID."""
    req = urllib.request.Request(url, headers=HEADERS)
    req.add_header('Cookie', f'POESESSID={poesessid}')
    return req


def _get(func):
    """
    Decorator function that returns (None, err) if an error occurs during an API call
    that involves a GET request.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        assert isinstance(self, APIManager)
        try:
            return (func(self, *args, **kwargs), '')
        except HTTPError as e:
            if e.code == HTTPStatus.TOO_MANY_REQUESTS:
                # TODO: update rate limiting variables on success
                rules = e.headers.get('X-Rate-Limit-Rules').split(',')
                rule = 'client' if 'client' in rules else rules[0]
                rate_limits_str = e.headers.get(f'X-Rate-Limit-{rule}')
                retry_after = int(e.headers.get('Retry-After'))
                logger.warning('Received rate limits: %s', rate_limits_str)
                logger.info('Retry after: %s', retry_after)
                self.too_many_reqs(rate_limits_str, retry_after)
            return (None, f'HTTP Error {e.code} {e.reason}')
        except URLError as e:
            return (None, f'URL Error {e.reason}')

    return wrapper


class APIManager(ThreadManager):
    """Manages sending official API calls."""

    def __init__(self):
        ThreadManager.__init__(self, APIThread)

    @_get
    def get_leagues(self) -> List[str]:  # pylint: disable=no-self-use
        """Retrieves current leagues."""
        logger.info('Sending GET request for leagues')
        req = urllib.request.Request(URL_LEAGUES, headers=HEADERS)
        with urllib.request.urlopen(req) as conn:
            leagues = json.loads(conn.read())
            return [league['id'] for league in leagues]

    @_get
    def get_tab_info(  # pylint: disable=no-self-use
        self, username: str, poesessid: str, league: str
    ) -> Any:
        """Retrieves number of tabs."""
        logger.info('Sending GET request for num tabs')
        req = _elevated_request(URL_TAB_INFO.format(username, league), poesessid)
        with urllib.request.urlopen(req) as conn:
            tab_info = json.loads(conn.read())
            return tab_info

    @_get
    def get_tab_items(  # pylint: disable=no-self-use
        self, username: str, poesessid: str, league: str, tab_index: int
    ) -> Any:
        """Retrieves items from a specific tab."""
        logger.info('Sending GET request for tab %s', tab_index)
        req = _elevated_request(
            URL_TAB_ITEMS.format(username, league, tab_index), poesessid
        )
        with urllib.request.urlopen(req) as conn:
            tab = json.loads(conn.read())
            return tab

    @_get
    def get_character_list(  # pylint: disable=no-self-use
        self, poesessid: str, league: str
    ) -> List[str]:
        """Retrieves character list."""
        logger.info('Sending GET request for characters')
        req = _elevated_request(URL_CHARACTERS, poesessid)
        with urllib.request.urlopen(req) as conn:
            char_info = json.loads(conn.read())
            return [char['name'] for char in char_info if char['league'] == league]

    @_get
    def get_character_items(  # pylint: disable=no-self-use
        self, username: str, poesessid: str, character: str
    ) -> Any:
        """Retrieves character list."""
        logger.info('Sending GET request for character %s', character)
        req = _elevated_request(URL_CHAR_ITEMS.format(username, character), poesessid)
        # TODO: also get jewels from passive tree
        with urllib.request.urlopen(req) as conn:
            char = json.loads(conn.read())
            return char


class APIThread(RetrieveThread):
    """Thread that handles API calls."""

    output = pyqtSignal(Ret)

    def __init__(self, api_manager: APIManager) -> None:
        RetrieveThread.__init__(self, api_manager, RateLimiter(RATE_LIMITS))

    def service_success(self, ret: Ret) -> None:
        """Emits the API output."""
        self.output.emit(ret)
