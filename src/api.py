"""
Contains API related functions.
"""

import json
import math
import time
import urllib.request

from collections import deque
from datetime import datetime
from functools import wraps
from queue import Queue
from threading import Condition
from typing import Any, Callable, List, Optional, Tuple
from urllib.error import HTTPError, URLError

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget

# HTTPS request headers
HEADERS = {'User-Agent': 'stash-of-exile/0.1.0 (contact:brianluo999@gmail.com)'}

URL_LEAGUES = 'https://api.pathofexile.com/leagues?type=main&compact=1'
URL_TAB_NUM = (
    'https://pathofexile.com/character-window/get-stash-items?accountName={}&league={}'
)
URL_TAB_ITEMS = URL_TAB_NUM + '&tabNum={}'
URL_CHARACTERS = 'https://pathofexile.com/character-window/get-characters'
URL_CHAR_ITEMS = (
    'https://pathofexile.com/character-window/get-items?accountName={}&character={}'
)

# Default rate limit values
RATE_LIMITS = [(5.0, 5.0), (10.0, 10.0), (15.0, 10.0)]


def _get_time_ms() -> int:
    """Gets time in milliseconds
    (epoch doesn't matter since only used for relativity)."""
    return round(datetime.utcnow().timestamp() * 1000)


def _get(func):
    """Decorator function that returns (None, err) if an error
    occurs during an API call that involves a GET request."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Tuple[Any, str]:
        try:
            return (func(*args, **kwargs), '')
        except HTTPError as e:
            return (None, f'HTTP Error {e.code} {e.reason}')
        except URLError as e:
            return (None, f'URL Error {e.reason}')

    return wrapper


def _elevated_request(url: str, poesessid: str) -> urllib.request.Request:
    req = urllib.request.Request(url, headers=HEADERS)
    req.add_header('Cookie', f'POESESSID={poesessid}')
    return req


class APIManager:
    """Manages sending official API calls."""

    def __init__(self):
        self.queue: Queue = Queue()
        self.cond = Condition()
        self.api_thread = APIThread(self)
        self.api_thread.start()

    def kill_thread(self) -> None:
        """Kills the API thread."""
        self.cond.acquire()
        self.queue.put(None)
        self.cond.notify()
        self.cond.release()
        self.api_thread.wait()

    def insert(
        self, api_call: Callable, api_args: Tuple, cb_obj: QWidget, cb: Callable
    ) -> None:
        """Inserts an element into the API queue."""
        self.cond.acquire()
        self.queue.put((api_call, api_args, cb_obj, cb))
        self.cond.notify()
        self.cond.release()

    def consume(self) -> Optional[Tuple[QWidget, Callable, Tuple]]:
        """Consumes an element from the API queue (blocking)."""
        self.cond.acquire()
        while self.queue.qsize() == 0:
            self.cond.wait()

        ret = self.queue.get()
        # Signals to kill the thread
        if ret is None:
            return None

        # Process api call
        api_call, api_args, cb_obj, cb = ret
        args = self.__getattribute__(api_call.__name__)(*api_args)

        self.cond.release()
        return (cb_obj, cb, args)

    @staticmethod
    @_get
    def get_leagues() -> List[str]:
        """Retrieves current leagues."""
        print('Sending GET request for leagues')
        req = urllib.request.Request(URL_LEAGUES, headers=HEADERS)
        with urllib.request.urlopen(req) as conn:
            leagues = json.loads(conn.read())
            return [league['id'] for league in leagues]

    @staticmethod
    @_get
    def get_num_tabs(username: str, poesessid: str, league: str) -> int:
        """Retrieves number of tabs."""
        print('Sending GET request for num tabs')
        req = _elevated_request(URL_TAB_NUM.format(username, league), poesessid)
        with urllib.request.urlopen(req) as conn:
            tab_info = json.loads(conn.read())
            return tab_info.get('numTabs', 0)

    @staticmethod
    @_get
    def get_tab_items(
        username: str, poesessid: str, league: str, tab_index: int
    ) -> Any:
        """Retrieves items from a specific tab."""
        print(f'Sending GET request for tab {tab_index}')
        req = _elevated_request(
            URL_TAB_ITEMS.format(username, league, tab_index), poesessid
        )
        with urllib.request.urlopen(req) as conn:
            tab = json.loads(conn.read())
            return tab

    @staticmethod
    @_get
    def get_character_list(poesessid: str, league: str) -> List[str]:
        """Retrieves character list."""
        print('Sending GET request for characters')
        req = _elevated_request(URL_CHARACTERS, poesessid)
        with urllib.request.urlopen(req) as conn:
            char_info = json.loads(conn.read())
            return [char['name'] for char in char_info if char['league'] == league]

    @staticmethod
    @_get
    def get_character_items(username: str, poesessid: str, character: str) -> Any:
        """Retrieves character list."""
        print(f'Sending GET request for character {character}')
        req = _elevated_request(URL_CHAR_ITEMS.format(username, character), poesessid)
        # TODO: also get jewels from passive tree
        with urllib.request.urlopen(req) as conn:
            char = json.loads(conn.read())
            return char


class APIThread(QThread):
    """Thread that handles API calls."""

    output = pyqtSignal(object, object, object)

    def __init__(self, api_manager: APIManager) -> None:
        QThread.__init__(self)
        self.api_manager = api_manager
        self.update_rate_limits(RATE_LIMITS)
        self.deque = deque()

    def update_rate_limits(self, rate_limits: List[Tuple[float, float]]) -> None:
        self.rate_limits = rate_limits

    def run(self) -> None:
        """Runs the thread. Employs rate limiting using a dequeue."""
        while True:

            ret = self.api_manager.consume()
            if ret is None:
                # Signal to exit the thread
                break

            cb_obj, cb, args = ret
            self.output.emit(cb_obj, cb, args)
