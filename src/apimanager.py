"""
Contains API related functions.
"""

import json
import urllib.request

from queue import Queue
from threading import Condition
from typing import Any, Callable, List, Optional, Tuple

from PyQt6.QtWidgets import QWidget

from thread import APIThread

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
        self.queue.put((None, None, lambda: None, ()))
        self.cond.notify()
        self.cond.release()
        self.api_thread.wait()

    def insert(self, elem: str, cb_obj: QWidget, cb: Callable, *args) -> None:
        """Inserts an element into the API queue."""
        self.cond.acquire()
        self.queue.put((elem, cb_obj, cb, args))
        self.cond.notify()
        self.cond.release()

    def consume(self) -> Optional[Tuple[QWidget, Callable, Tuple]]:
        """Consumes an element from the API queue (blocking)."""
        self.cond.acquire()
        while self.queue.qsize() == 0:
            self.cond.wait()
        elem, cb_obj, cb, args = self.queue.get()

        # Signals to kill the thread
        if elem is None:
            return None
        assert cb_obj is not None

        # Process element
        print(elem)
        self.cond.release()
        return (cb_obj, cb, args)

    @staticmethod
    def get_leagues() -> List[str]:
        """Retrieves current leagues."""
        print('Sending GET request for leagues')
        req = urllib.request.Request(URL_LEAGUES, headers=HEADERS)
        with urllib.request.urlopen(req) as conn:
            leagues = json.loads(conn.read())
            return [league['id'] for league in leagues]

    @staticmethod
    def get_num_tabs(username: str, poesessid: str, league: str) -> int:
        """Retrieves number of tabs."""
        print('Sending GET request for num tabs')
        req = _elevated_request(URL_TAB_NUM.format(username, league), poesessid)
        with urllib.request.urlopen(req) as conn:
            tab_info = json.loads(conn.read())
            return tab_info.get('numTabs', 0)

    @staticmethod
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
    def get_character_list(poesessid: str, league: str) -> List[str]:
        """Retrieves character list."""
        print('Sending GET request for characters')
        req = _elevated_request(URL_CHARACTERS, poesessid)
        with urllib.request.urlopen(req) as conn:
            char_info = json.loads(conn.read())
            return [char['name'] for char in char_info if char['league'] == league]

    @staticmethod
    def get_character_items(username: str, poesessid: str, character: str) -> Any:
        """Retrieves character list."""
        print(f'Sending GET request for character {character}')
        req = _elevated_request(URL_CHAR_ITEMS.format(username, character), poesessid)
        # TODO: also get jewels from passive tree
        with urllib.request.urlopen(req) as conn:
            char = json.loads(conn.read())
            return char
