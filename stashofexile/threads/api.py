"""
Contains API related classes.
"""

import functools
import http
import json
import urllib.error
import urllib.request
from typing import Any, List, Tuple

from PyQt6.QtCore import pyqtSignal

from stashofexile import consts, log
from stashofexile.threads import ratelimiting, thread

logger = log.get_logger(__name__)

# HTTPS request headers
HEADERS = {
    'User-Agent': f'stash-of-exile/{consts.VERSION} (contact:brianluo999@gmail.com)'
}

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
URL_UNIQUE = 'https://www.pathofexile.com/account/view-stash/{}/{}/{}'


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
        assert isinstance(self, APIThread)
        try:
            ret = (func(self, *args, **kwargs), '')
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
            ret = (None, f'HTTP Error {e.code} {e.reason} {func.__name__}')
        except urllib.error.URLError as e:
            ret = (None, f'URL Error {e.reason} {func.__name__}')

        return ret

    return wrapper


class APIThread(thread.RetrieveThread):
    """Thread that handles API calls."""

    output = pyqtSignal(thread.Ret)
    status_output = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__(ratelimiting.RateLimiter(RATE_LIMITS))

    def service_success(self, ret: thread.Ret) -> None:
        """Emits the API output."""
        self.output.emit(ret)

    def rate_limit(self, message: str) -> None:
        """Emits status update."""
        self.status_output.emit(message)

    @_get
    def get_leagues(self) -> List[str]:  # pylint: disable=no-self-use
        """Retrieves current leagues."""
        logger.info('Sending GET request for leagues')
        req = urllib.request.Request(URL_LEAGUES, headers=HEADERS)
        with urllib.request.urlopen(req) as response:
            leagues = json.loads(response.read())
            return [league['id'] for league in leagues]

    @_get
    def get_tab_info(  # pylint: disable=no-self-use
        self, username: str, poesessid: str, league: str
    ) -> Any:
        """Retrieves number of tabs."""
        logger.info('Sending GET request for num tabs')
        req = _elevated_request(
            URL_TAB_ITEMS.format(username, league, 0).replace(' ', '%20'), poesessid
        )
        with urllib.request.urlopen(req) as response:
            tab_info = json.loads(response.read())
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
        with urllib.request.urlopen(req) as response:
            tab = json.loads(response.read())
            return tab

    @_get
    def get_character_list(  # pylint: disable=no-self-use
        self, poesessid: str, league: str
    ) -> List[str]:
        """Retrieves character list."""
        logger.info('Sending GET request for characters')
        req = _elevated_request(URL_CHARACTERS, poesessid)
        with urllib.request.urlopen(req) as response:
            char_info = json.loads(response.read())
            return [char['name'] for char in char_info if char['league'] == league]

    @_get
    def get_character_items(  # pylint: disable=no-self-use
        self, username: str, poesessid: str, character: str
    ) -> Any:
        """Retrieves character list."""
        logger.info('Sending GET request for character %s', character)
        req = _elevated_request(URL_CHAR_ITEMS.format(username, character), poesessid)
        with urllib.request.urlopen(req) as response:
            char = json.loads(response.read())
            return char

    @_get
    def get_character_jewels(  # pylint: disable=no-self-use
        self, username: str, poesessid: str, character: str
    ) -> Any:
        """Retrieves socketed jewels in a character."""
        logger.info('Sending GET request for character jewels %s', character)
        req = _elevated_request(URL_PASSIVE_TREE.format(username, character), poesessid)
        with urllib.request.urlopen(req) as response:
            tree = json.loads(response.read())
            return tree

    @_get
    def get_unique_subtab(  # pylint: disable=no-self-use
        self, username: str, uid: str, tab_index: int
    ) -> Any:
        """Retrieves items from unique subtab."""
        req = urllib.request.Request(
            URL_UNIQUE.format(username, uid, tab_index), headers=HEADERS
        )
        logger.info(
            'Sending GET request for unique subtab %s %s', tab_index, req.full_url
        )
        with urllib.request.urlopen(req) as response:
            encoding = response.info().get_param('charset', 'utf-8')
            return response.read().decode(encoding)
