"""
Constants that do not involve game data (found in gamedata.py).
"""

import os
import sys

from PyQt6.QtCore import QSettings

from stashofexile import file

VERSION = '0.2.0'

# Assets directory
if getattr(sys, 'frozen', False):
    app_path = os.path.dirname(sys.executable)
else:
    app_path = os.path.dirname(os.path.dirname(__file__))

ASSETS_DIR = os.path.join(app_path, 'assets')
ITEM_TYPE_SRC = 'assets/item_type'

# Milliseconds for status bar to timeout
STATUS_TIMEOUT = 10000

# Template to color tooltips
SPAN_TEMPLATE = '<span style="color:{}">{}</span>'

# Template for item name headers
HEADER_TEMPLATE = (
    '<h3 style="font-weight: normal; text-align: center; margin: 0px;">{}</h3>'
)

# Template for item tooltip separator
SEPARATOR_TEMPLATE = '<img src="{}" width="{}" />'

# Template for standard image
IMG_TEMPLATE = '<img src="{}" />'

# Named color/type to color or hex
COLORS = {
    # Generic colors
    'white': '#ffffff',
    'grey': '#777777',
    'middarkgrey': '#5a5a5a',
    'darkgrey': '#242424',
    # Item rarities
    'normal': '#ffffff',
    'magic': '#8888ff',
    'rare': '#ffff77',
    'unique': '#af6025',
    'gem': '#1ba29b',
    'currency': '#aa9e82',
    'divination': '#04adea',
    'quest': '#4ae63a',
    'prophecy': '#b049f8',
    'foil': '#82ad6a',
    # Other
    'red': '#ac0100',
    'craft': '#b4b4ff',
    'fire': '#960000',
    'lightning': 'gold',
    'cold': '#366492',
    'chaos': '#d02090',
    'scourged': '#ff6e25',
}

# Rarity to frame type
FRAME_TYPES = {
    'normal': 'SeparatorWhite.png',
    'magic': 'SeparatorMagic.png',
    'rare': 'SeparatorRare.png',
    'unique': 'SeparatorUnique.png',
    'gem': 'SeparatorGem.png',
    'currency': 'SeparatorCurrency.png',
}

# API value to named color/type
VALNUM_TO_COLOR = {
    0: 'white',
    1: 'magic',
    2: 'red',
    3: 'white',  # physical
    4: 'fire',
    5: 'cold',
    6: 'lightning',
    7: 'chaos',
    8: 'magic',
    9: 'rare',
    10: 'unique',
    15: 'middarkgrey',
    16: 'white',
    18: 'currency',
    19: 'white',
    20: 'divination',
}

_settings = QSettings(
    QSettings.Format.IniFormat,
    QSettings.Scope.UserScope,
    'StashOfExile',
    'StashOfExile',
).fileName()
APPDATA_DIR = os.path.dirname(_settings)
file.create_directories(_settings)
