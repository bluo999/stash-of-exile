"""
Constants that involve game data.
"""
import json
import os

from typing import Dict, List

from stashofexile import consts

INFLUENCES = ['shaper', 'elder', 'crusader', 'hunter', 'redeemer', 'warlord']

# API rarity number to named rarity
RARITIES = {
    0: 'normal',
    1: 'magic',
    2: 'rare',
    3: 'unique',
    4: 'gem',
    5: 'currency',
    6: 'divination',
    7: 'quest',
    8: 'prophecy',
    9: 'foil',
}

# Keywords in fragment items
FRAGMENTS = {
    'Sacrifice at',
    'Mortal ',
    '\'s Key',
    'Fragment of ',
    ' Breachstone',
    ' Emblem',
    ' to the Goddess',
    ' Vessel',
    'The Maven\'s Writ',
    'Sacred Blossom',
}

# Unique tab categories
UNIQUE_CATEGORIES: Dict[int, str] = {
    1: 'Flask',
    2: 'Amulet',
    3: 'Ring',
    4: 'Claw',
    5: 'Dagger',
    6: 'Wand',
    7: 'Sword',
    8: 'Axe',
    9: 'Mace',
    10: 'Bow',
    11: 'Staff',
    12: 'Quiver',
    13: 'Belt',
    14: 'Gloves',
    15: 'Boots',
    16: 'Body Armour',
    17: 'Helmet',
    18: 'Shield',
    19: 'Map',
    20: 'Jewel',
    22: 'Contract',
}

# Selectable options for ComboBox filters
COMBO_ITEMS = {
    'Rarity': ['Normal', 'Magic', 'Rare', 'Unique', 'Foil', 'Any Non-Unique'],
    'Category': [
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
        'Skill Gem',
        'Support Gem',
        'Jewel',
        'Abyss Jewel',
        'Cluster Jewel',
        'Flask',
        'Map',
        'Map Fragment',
        'Maven\'s Invitation',
        'Scarab',
        'Watchstone',
        'Leaguestone',
        'Prophecy',
        'Divination Card',
        'Captured Beast',
        'Metamorph Sample',
        'Contract',
        'Blueprint',
        'Currency',
        'Unique Fragment',
        'Resonator',
        'Fossil',
        'Incubator',
        'Heist',
        'Inscribed Ultimatum',
        'Expedition Logbook',
        'Sentinel',
        'Quest',
    ],
    'Character Class': [
        'Scion',
        'Marauder',
        'Ranger',
        'Witch',
        'Duelist',
        'Templar',
        'Shadow',
    ],
    'Gem Quality Type': [
        'Superior (Default)',
        'Any Alternate',
        'Anomalous',
        'Divergent',
        'Phantasmal',
    ],
}

ALTERNATE_QUALITIES = COMBO_ITEMS['Gem Quality Type'][-3:]

GEM_CATEGORIES = {'Skill Gem', 'Support Gem'}

PARSE_CATEGORIES = {
    'Incubator',
    'Quiver',
    'Amulet',
    'Ring',
    'Belt',
    'Trinket',
    'Cluster Jewel',
    'Jewel',
    'Flask',
    'Map',
    'Maven\'s Invitation',
    'Scarab',
    'Watchstone',
    'Leaguestone',
    'Contract',
    'Blueprint',
    'Resonator',
    'Fossil',
    'Inscribed Ultimatum',
    'Expedition Logbook',
    'Sentinel',
}

BASES_FILE = os.path.join(consts.ASSETS_DIR, 'bases.json')
with open(BASES_FILE, 'rb') as f:
    BASE_TYPES: Dict[str, List[str]] = json.load(f)

ALTART_FILE = os.path.join(consts.ASSETS_DIR, 'altart.json')
with open(ALTART_FILE, 'rb') as f:
    ALTART: List[str] = json.load(f)
