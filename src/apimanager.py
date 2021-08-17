"""
Contains API related functions.
"""

import json
from typing import List
import urllib.request

from consts import HEADERS

from save import Account

URL_LEAGUES = 'https://api.pathofexile.com/leagues?type=main&compact=1'
URL_TABS = (
    'https://pathofexile.com/character-window/get-stash-items?accountName={}&league={}'
)
URL_CHARACTERS = 'https://pathofexile.com/character-window/get-characters'


class APIManager:
    """Manages sending official API calls."""

    @staticmethod
    def get_leagues() -> List[str]:
        """Retrieve leagues by sending a GET to Path of Exile API."""
        print('Sending GET request for leagues')
        req = urllib.request.Request(URL_LEAGUES, headers=HEADERS)
        with urllib.request.urlopen(req) as conn:
            leagues = json.loads(conn.read())
            return [league['id'] for league in leagues]

    @staticmethod
    def get_num_tabs(account: Account, league: str) -> int:
        """Retrieve number of tabs by sending a GET."""
        print('Sending GET request for num tabs')
        req = urllib.request.Request(
            URL_TABS.format(account.username, league), headers=HEADERS
        )
        req.add_header('Cookie', f'POESESSID={account.poesessid}')
        with urllib.request.urlopen(req) as conn:
            tab_info = json.loads(conn.read())
            return tab_info['numTabs']

    @staticmethod
    def get_character_list(account: Account, league: str) -> List[str]:
        """Retrieve character list by sending a GET."""
        print('Sending GET request for characters')
        req = urllib.request.Request(URL_CHARACTERS, headers=HEADERS)
        req.add_header('Cookie', f'POESESSID={account.poesessid}')
        with urllib.request.urlopen(req) as conn:
            char_info = json.loads(conn.read())
            return [char['name'] for char in char_info if char['league'] == league]
