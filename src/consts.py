# Milliseconds for status bar to timeout
STATUS_TIMEOUT = 5000

SPAN_TEMPLATE = """<span style="color:{}">{}</span>"""

HEADER_TEMPLATE = """
<h3 style="
    font-weight: normal;
    text-align: center;
    padding: 0px;
    margin: 0px;">
    {}
</h3>"""

TOOLTIP_TEMPLATE = """
<div style="
    height: 100%;
    background-repeat: no-repeat;
    background-image: url({});">
</div>"""

SEPARATOR_TEMPLATE = """<img src="{}" width="{}" />"""

COLORS = {
    # Generic colors
    'white': 'white',
    'grey': '#777777',
    # Item rarities
    'normal': 'white',
    'magic': '#8888ff',
    'rare': '#ffff77',
    'unique': '#af6021',
    'gem': '#1ba29b',
    'currency': '#aa9e82',
    'divination': '#04adea',
    'prophecy': '#b049f8',
    'foil': '#82ad6a',
    # Other
    'red': '#ac0100',
    'craft': '#b4b4ff',
    'fire': '#710000',
}

VALNUM_TO_COLOR = {0: 'white', 1: 'magic', 4: 'fire'}
