"""
Contains API related functions.
"""

from dataclasses import dataclass
import json
import math
import time
import urllib.request

from collections import deque
from datetime import datetime
from functools import wraps
from http import HTTPStatus
from threading import Condition
from typing import Any, Callable, Deque, List, Tuple, Union
from urllib.error import HTTPError, URLError

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget

import log

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
RATE_LIMITS = [(45, 60000), (240, 240000)]


@dataclass
class TooManyReq:
    """Class storing data from a too many requests HTTP error."""

    rate_limits: List[Tuple[int, int]]
    retry_after: int


def _get_time_ms() -> int:
    """Gets time in milliseconds
    (epoch doesn't matter since only used for relativity)."""
    return round(datetime.utcnow().timestamp() * 1000)


def _elevated_request(url: str, poesessid: str) -> urllib.request.Request:
    """Wraps a request that requires POESESSID."""
    req = urllib.request.Request(url, headers=HEADERS)
    req.add_header('Cookie', f'POESESSID={poesessid}')
    return req


def _get(func):
    """Decorator function that returns (None, err) if an error
    occurs during an API call that involves a GET request."""

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


class APIManager:
    """Manages sending official API calls."""

    def __init__(self):
        Elem = Union[TooManyReq, Tuple[Callable, Tuple, QWidget, Callable, Tuple], None]
        self.queue: Deque[Elem] = deque()
        self.cond = Condition()
        self.api_thread = APIThread(self)
        self.api_thread.start()

    def kill_thread(self) -> None:
        """Kills the API thread."""
        self.cond.acquire()
        self.queue.append(None)
        self.cond.notify()
        self.cond.release()
        self.api_thread.wait()

    def too_many_reqs(self, rate_limits_str: str, retry_after: int) -> None:
        """Updates the rate limits based on the string from response headers."""
        rate_limits: List[Tuple[int, int]] = []
        for rate_limit in rate_limits_str.split(','):
            hits, period, _ = rate_limit.split(':')
            rate_limits.append((int(hits), int(period) * 1000))
        self.cond.acquire()
        self.queue.appendleft(TooManyReq(rate_limits, retry_after))
        self.cond.notify()
        self.cond.release()

    def insert(
        self,
        api_call: Callable,
        api_args: Tuple,
        cb_obj: QWidget,
        cb: Callable,
        cb_args: Tuple,
    ) -> None:
        """Inserts an element into the API queue."""
        # TODO: batch insert
        self.cond.acquire()
        self.queue.append((api_call, api_args, cb_obj, cb, cb_args))
        self.cond.notify()
        self.cond.release()

    def consume(
        self
    ) -> Union[TooManyReq, Tuple[QWidget, Callable, Tuple, Tuple], None]:
        """Consumes an element from the API queue (blocking)."""
        self.cond.acquire()
        while len(self.queue) == 0:
            self.cond.wait()

        ret = self.queue.popleft()
        # Signals to kill the thread
        if ret is None:
            return None

        if isinstance(ret, TooManyReq):
            return ret

        # Process api call
        api_call, api_args, cb_obj, cb, cb_args = ret
        args = self.__getattribute__(api_call.__name__)(*api_args)

        self.cond.release()
        return (cb_obj, cb, cb_args, args)

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


class APIQueue(deque):
    """Queue that stores API call timestamps for rate limiting purposes."""

    def __init__(self, hits: int = 0, period: int = 0):
        deque.__init__(self)
        self.update_rate_limit(hits, period)

    def update_rate_limit(self, hits: int, period: int):
        """Update to new rate limits."""
        self.hits = hits
        self.period = period


class APIQueueManager:
    """Keeps track of multiple API Queues."""

    def __init__(self, rate_limits: List[Tuple[int, int]]):
        self.queues = [APIQueue(hits, period) for hits, period in rate_limits]

    def update_rate_limits(self, rate_limits: List[Tuple[int, int]]) -> None:
        """Update to new rate limits."""
        if len(rate_limits) < len(self.queues):
            self.queues = self.queues[: len(rate_limits)]
        elif len(rate_limits) > len(self.queues):
            for _ in range(len(rate_limits) - len(self.queues)):
                self.queues.append(APIQueue())

        for queue, (hits, period) in zip(self.queues, rate_limits):
            queue.update_rate_limit(hits, period)

    def insert(self) -> None:
        """Add timestamp to queue."""
        for queue in self.queues:
            queue.append(_get_time_ms())

    def block_until_ready(self) -> None:
        """Sleeps until the next API call won't be rejected (if necessary)."""
        if all(len(queue) < queue.hits for queue in self.queues):
            return

        # Pop excess elements (needed when rate limits change)
        for queue in self.queues:
            num_iters = len(queue) - queue.hits
            for _ in range(num_iters):
                queue.popleft()

        assert all(len(queue) <= queue.hits for queue in self.queues)
        next_avail_time = max(
            queue.popleft() + queue.period
            for queue in self.queues
            if len(queue) == queue.hits
        )
        sleep_time = max((next_avail_time - _get_time_ms()) / 1000, 0.0)
        if math.isclose(sleep_time, 0.0):
            return

        if sleep_time > 1.0:
            logger.info('Cooling off API calls for %s', sleep_time)
        time.sleep(sleep_time)


class APIThread(QThread):
    """Thread that handles API calls."""

    output = pyqtSignal(object, object, object, object)

    def __init__(self, api_manager: APIManager) -> None:
        QThread.__init__(self)
        self.api_manager = api_manager
        self.api_queue_manager = APIQueueManager(RATE_LIMITS)

    def run(self) -> None:
        """Runs the thread."""
        while True:
            self.api_queue_manager.block_until_ready()
            ret = self.api_manager.consume()
            self.api_queue_manager.insert()
            if ret is None:
                # Signal to exit the thread
                break
            if isinstance(ret, TooManyReq):
                self.api_queue_manager.update_rate_limits(ret.rate_limits)
                logger.warning('Hit rate limit, sleeping for %s', ret.retry_after)
                time.sleep(ret.retry_after)
                continue

            cb_obj, cb, cb_args, args = ret
            self.output.emit(cb_obj, cb, cb_args, args)
