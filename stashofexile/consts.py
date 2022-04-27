"""
Constants that do not involve game data (found in gameData.py).
"""

# Milliseconds for status bar to timeout
STATUS_TIMEOUT = 10000

# Template to color tooltips
SPAN_TEMPLATE = """<span style="color:{}">{}</span>"""

# Template for item name headers
HEADER_TEMPLATE = """
<h3 style="
    font-weight: normal;
    text-align: center;
    padding: 0px;
    margin: 0px;">
    {}
</h3>
"""

# Template for item tooltip separator
SEPARATOR_TEMPLATE = """<img src="{}" width="{}" />"""

# Named color/type to color or hex
COLORS = {
    # Generic colors
    'white': '#ffffff',
    'grey': '#777777',
    'darkgrey': '#242424',
    # Item rarities
    'normal': '#ffffff',
    'magic': '#8888ff',
    'rare': '#ffff77',
    'unique': '#af6025',
    'gem': '#1ba29b',
    'currency': '#aa9e82',
    'divination': '#04adea',
    'prophecy': '#b049f8',
    'foil': '#82ad6a',
    # Other
    'red': '#ac0100',
    'craft': '#b4b4ff',
    'fire': '#960000',
    'lightning': 'gold',
    'cold': '#366492',
    'chaos': '#d02090',
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
    16: 'white',
}
