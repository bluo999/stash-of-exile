"""
Handles item tabs (character or stash tabs).
"""

import abc
import json

from typing import List, Optional

from stashofexile import log, util
from stashofexile.items import item

logger = log.get_logger(__name__)


class ItemTab(abc.ABC):
    """
    Represents any type of tab (character or stash).

    Note that ItemTab does not retrieve items on construction, as the file may not
    exist yet (if an API call is going to be used).
    """

    def __init__(self, filepath: str):
        self.filepath = filepath

    def __repr__(self):
        return self.get_tab_name()

    def get_items(self) -> List[item.Item]:
        """Gets items from this tab."""
        tab_items: List[item.Item] = []
        with open(self.filepath, 'r') as f:
            data = json.load(f)
            self._parse_data(data)
            tab_name = self.get_tab_name()
            # Add each item
            for item_data in data['items']:
                tab_items.append(item.Item(item_data, tab_name))
                # Add socketed items
                if item_data.get('socketedItems') is not None:
                    for socketed_item in item_data['socketedItems']:
                        tab_items.append(item.Item(socketed_item, tab_name))
        tab_items.sort()
        return tab_items

    @abc.abstractmethod
    def get_tab_name(self) -> str:
        """Gets a tab's name."""

    @abc.abstractmethod
    def _parse_data(self, data) -> None:
        """Parses a tab's data."""


class CharacterTab(ItemTab):
    """Represents a character's items."""

    def __init__(self, filepath: str, char_name: Optional[str] = None):
        super().__init__(filepath)
        self.char_name = (
            util.get_file_name(filepath) if char_name is None else char_name
        )

    def get_tab_name(self) -> str:
        return self.char_name

    def _parse_data(self, data) -> None:
        """Don't need to parse the tab."""


class StashTab(ItemTab):
    """Represents a stash tab's items."""

    def __init__(self, filepath: str, tab_num: Optional[int] = None):
        super().__init__(filepath)
        self.tab_num = int(util.get_file_name(filepath)) if tab_num is None else tab_num
        self.tab_name: str = ''

    def get_tab_name(self) -> str:
        return f'{self.tab_num} ({self.tab_name})'

    def _parse_data(self, data) -> None:
        self.tab_name = data['tabs'][self.tab_num]['n']
