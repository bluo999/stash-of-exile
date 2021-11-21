"""
Constants that involve game data.
"""
import json

from typing import Dict, List

# API rarity number to named rarity
RARITIES = {
    0: 'normal',
    1: 'magic',
    2: 'rare',
    3: 'unique',
    4: 'gem',
    5: 'currency',
    6: 'divination',
    8: 'prophecy',
    9: 'foil',
}

# Keywords in fragment items
FRAGMENTS = [
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
]

# Selectable options for ComboBox filters
COMBO_ITEMS = {
    'Rarity': ['Any', 'Normal', 'Magic', 'Rare', 'Unique', 'Foil', 'Any Non-Unique'],
    'Category': [
        'Any',
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
        '',
    ],
}

PARSE_CATEGORIES = [
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
]

with open('bases.json', 'rb') as f:
    BASE_TYPES: Dict[str, List[str]] = json.load(f)
