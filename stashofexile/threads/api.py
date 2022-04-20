"""
Contains API related classes.
"""

import functools
import http
import json
import urllib.request
import urllib.error

from typing import Any, List, Tuple

from PyQt6.QtCore import pyqtSignal

from stashofexile import log
from stashofexile.threads import ratelimiting, thread

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
URL_PASSIVE_TREE = (
    'https://pathofexile.com/character-window/get-passive-skills?'
    'accountName={}&character={}&reqData=0'
)


# Default rate limit values (hits, period (in ms))
RATE_LIMITS = [ratelimiting.RateLimit(45, 60000), ratelimiting.RateLimit(240, 240000)]


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

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs) -> Tuple:
        assert isinstance(self, APIManager)
        try:
            return (func(self, *args, **kwargs), '')
        except urllib.error.HTTPError as e:
            if e.code == http.HTTPStatus.TOO_MANY_REQUESTS:
                rules = e.headers.get('X-Rate-Limit-Rules').split(',')
                rule = 'client' if 'client' in rules else rules[0]
                rate_limits_str = e.headers.get(f'X-Rate-Limit-{rule}')
                retry_after = int(e.headers.get('Retry-After'))
                logger.warning('Received rate limits: %s', rate_limits_str)
                logger.info('Retry after: %s', retry_after)
                rate_limits: List[ratelimiting.RateLimit] = []
                for rate_limit in rate_limits_str.split(','):
                    hits, period, _ = rate_limit.split(':')
                    rate_limits.append(
                        ratelimiting.RateLimit(int(hits), int(period) * 1000)
                    )
                self.too_many_reqs(rate_limits, retry_after)
            return (None, f'HTTP Error {e.code} {e.reason}')
        except urllib.error.URLError as e:
            return (None, f'URL Error {e.reason}')

    return wrapper


class APIManager(thread.ThreadManager):
    """Manages sending official API calls."""

    def __init__(self):
        super().__init__(APIThread)
        # Guarantee type to be APIThread
        self.thread: APIThread = self.thread

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
        req = _elevated_request(
            URL_TAB_INFO.format(username, league).replace(' ', '%20'), poesessid
        )
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
            URL_TAB_ITEMS.format(username, league, tab_index).replace(' ', '%20'),
            poesessid,
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
        with urllib.request.urlopen(req) as conn:
            char = json.loads(conn.read())
            return char

    @_get
    def get_character_jewels(  # pylint: disable=no-self-use
        self, username: str, poesessid: str, character: str
    ) -> Any:
        """Retrieves socketed jewels in a character."""
        logger.info('Sending GET request for character jewels %s', character)
        req = _elevated_request(URL_PASSIVE_TREE.format(username, character), poesessid)
        with urllib.request.urlopen(req) as conn:
            tree = json.loads(conn.read())
            return tree


class APIThread(thread.RetrieveThread):
    """Thread that handles API calls."""

    output = pyqtSignal(thread.Ret)

    def __init__(self, api_manager: APIManager) -> None:
        super().__init__(api_manager, ratelimiting.RateLimiter(RATE_LIMITS))

    def service_success(self, ret: thread.Ret) -> None:
        """Emits the API output."""
        self.output.emit(ret)
