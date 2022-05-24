"""
Defines the database used to store mods.
"""

import re

from typing import List, NamedTuple

from stashofexile.items import item as m_item

MOD_CATEGORIES = [
    'Bow',
    'Claw',
    'Dagger',
    'Rune Dagger',
    'One Handed Axe',
    'One Handed Mace',
    'One Handed Sword',
    'Sceptre',
    'Staff',
    'Warstaff',
    'Two Handed Axe',
    'Two Handed Mace',
    'Two Handed Sword',
    'Wand',
    'Fishing Rod',
    'Body Armour',
    'Boots',
    'Gloves',
    'Helmet',
    'Shield',
    'Quiver',
    'Amulet',
    'Ring',
    'Belt',
    'Trinket',
    'Jewel',
    'Abyss Jewel',
    'Cluster Jewel',
    'Flask',
    'Map',
    'Maven\'s Invitation',
    'Watchstone',
    'Leaguestone',
    'Contract',
    'Blueprint',
    'Heist',
    'Expedition Logbook',
    'Sentinel',
]

NUMERIC_REGEX = r'(\d+(\.\d+)?(\d+)?)'


class Mod(NamedTuple):
    """Represents an item mod."""

    key: str
    values: List[float]


def _parse_mod(mod_str: str) -> Mod:
    """Parses a mod string and returns Mod, with numeric values extracted."""
    values = [float(x) for x, _, _ in re.findall(NUMERIC_REGEX, mod_str) if x != '']
    key = re.sub(NUMERIC_REGEX, '#', mod_str)
    return Mod(key.replace('\n', ' '), values)


class ModDb(dict):
    """Represents a mod database which stores mods."""

    def insert_items(self, items: List[m_item.Item]) -> None:
        """
        Inserts items' mods into the db. Also adds a field which makes them suitable for
        searching.
        """
        for item in items:
            if item.category not in MOD_CATEGORIES:
                continue
            mod_groups = (
                item.implicit,
                item.scourge,
                item.fractured,
                item.explicit,
                item.crafted,
                item.enchanted,
            )
            for mod_group in mod_groups:
                for mod_str in mod_group:
                    mod = _parse_mod(mod_str)
                    item.internal_mods[mod.key] = mod.values
                    self[mod.key] = len(mod.values)
