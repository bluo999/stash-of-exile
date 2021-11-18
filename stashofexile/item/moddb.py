"""
Defines the database used to store mods.
"""

from typing import List

from item.item import Item


class ModDb(dict):
    """Stores mods."""

    def insert_items(self, items: List[Item]) -> None:
        """
        Inserts items' mods into the db. Also adds a field which makes them
        suitable for searching.
        """
        for item in items:
            if item.category != 'Boots':
                continue
            for mod in item.explicit:
                item.internal_mods[mod] = 0
                self[mod] = 0
