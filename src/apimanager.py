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
    @staticmethod
    def getLeagues() -> List[str]:
        """Retrieve leagues by sending a GET to Path of Exile API."""
        print('Sending GET request for leagues')
        req = urllib.request.Request(URL_LEAGUES, headers=HEADERS)
        r = urllib.request.urlopen(req)
        return [league['id'] for league in json.loads(r.read())]

    @staticmethod
    def getNumTabs(account: Account, league: str) -> int:
        """Retrieve number of tabs by sending a GET."""
        print('Sending GET request for num tabs')
        req = urllib.request.Request(
            URL_TABS.format(account.username, league), headers=HEADERS
        )
        req.add_header('Cookie', f'POESESSID={account.poesessid}')
        r = urllib.request.urlopen(req)
        return json.loads(r.read())['numTabs']

    @staticmethod
    def getCharacterList(account: Account, league: str) -> List[str]:
        """Retrieve character list by sending a GET."""
        print('Sending GET request for characters')
        req = urllib.request.Request(URL_CHARACTERS, headers=HEADERS)
        req.add_header('Cookie', f'POESESSID={account.poesessid}')
        r = urllib.request.urlopen(req)
        return [
            char['name'] for char in json.loads(r.read()) if char['league'] == league
        ]
