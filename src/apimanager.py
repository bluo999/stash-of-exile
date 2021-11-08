"""
Contains API related functions.
"""

import json

from typing import Any, Dict, List

import urllib.request

from save import Account

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
    ) -> List[Dict[str, Any]]:
        """Retrieves items from a specific tab."""
        print(f'Sending GET request for tab {tab_index}')
        req = _elevated_request(
            URL_TAB_ITEMS.format(username, league, tab_index), poesessid
        )
        with urllib.request.urlopen(req) as conn:
            tab = json.loads(conn.read())
            return tab.get('items', [])

    @staticmethod
    def get_character_list(poesessid: str, league: str) -> List[str]:
        """Retrieves character list."""
        print('Sending GET request for characters')
        req = _elevated_request(URL_CHARACTERS, poesessid)
        with urllib.request.urlopen(req) as conn:
            char_info = json.loads(conn.read())
            return [char['name'] for char in char_info if char['league'] == league]

    @staticmethod
    def get_character_items(
        username: str, poesessid: str, character: str
    ) -> List[Dict[str, Any]]:
        """Retrieves character list."""
        print('Sending GET request for characters')
        req = _elevated_request(URL_CHAR_ITEMS.format(username, character), poesessid)
        # TODO: also get jewels from passive tree
        with urllib.request.urlopen(req) as conn:
            char = json.loads(conn.read())
            return char.get('items', [])
