"""
Defines Item class, responsible for:
 - parsing item API and converting into a local object
 - generating properties used for filtering
 - generating tooltips for display
"""

import os
import re
from typing import Any, Callable, Dict, List, NamedTuple, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPainter, QPixmap

from stashofexile import consts, gamedata, log, util
from stashofexile.items import property as m_property
from stashofexile.items import requirement
from stashofexile.items import socket as m_socket

logger = log.get_logger(__name__)

PLUS_PERCENT_REGEX = re.compile(r'\+(\d+)%')  # +x%
PERCENT_REGEX = re.compile(r'(\d+)%')  # x%
NUMBER_REGEX = re.compile(r'(\d+)')
FLAT_PERCENT_REGEX = re.compile(r'([0-9]{1,2}\.\d{2})%')  # xx.xx%
NUM_RANGE_REGEX = re.compile(r'(\d+)-(\d+)')  # x-x

BR_REGEX = re.compile(r'<br />')
CLEAN_REGEX = re.compile(r'<.*?>')

IMAGE_CACHE_DIR = os.path.join(consts.APPDATA_DIR, 'image_cache')
SOCKET_DIR = os.path.join(consts.ASSETS_DIR, 'socket')
SOCKET_FILE = os.path.join(SOCKET_DIR, 'Socket{}.png')

SOCKET_PX = 47
LINK_LENGTH = 38
LINK_WIDTH = 16


class ModGroup(NamedTuple):
    """Represents a mod group (e.g. explicit, crafted)."""

    mods: List[str]
    color: str


class Tag(NamedTuple):
    """Represents a tag (e.g. mirrored, corrupted)."""

    name: str
    color: str
    active: bool


def _list_mods(mod_groups: List[ModGroup]) -> str:
    """Returns a single line-separated, colored string of mods."""
    # Get rid of any empty mod list
    filt_mod_lists = [
        ModGroup(mod_group.mods, mod_group.color)
        for mod_group in mod_groups
        if mod_group.mods
    ]

    if not filt_mod_lists:
        return ''

    # Split mods that have \n
    for mods, _ in filt_mod_lists:
        i = 0
        length = len(mods)
        while i < length:
            while '\n' in mods[i]:
                # Split into two elements and move to the second element
                index = mods[i].index('\n')
                mods.insert(i + 1, mods[i][index + 1 :])
                mods[i] = mods[i][:index]
                length += 1
            i += 1

    # Colorize and split mods on separate lines
    text: List[str] = []
    for i, (mods, color) in enumerate(filt_mod_lists):
        for j, mod in enumerate(mods):
            text.append(util.colorize(mod, color))
            if i < len(filt_mod_lists) - 1 or j < len(mods) - 1:
                text.append('<br />')

    return ''.join(text)


def _list_tags(tag_info: List[Tag]) -> str:
    """Returns a single line-separated, colored string of tags."""
    # Get rid of inactive tags then format them
    formatted_tags = [
        util.colorize(tag.name, tag.color) for tag in tag_info if tag.active
    ]

    # Add tags on separate lines
    text: List[str] = []
    for i, tag in enumerate(formatted_tags):
        text.append(tag)
        if i < len(formatted_tags) - 1:
            text.append('<br />')

    return ''.join(text)


def _draw_2width_links(
    painter: QPainter, i: int, row: int, link_v: QImage, link_h: QImage
) -> None:
    """Draws links for a 2 width item depending on socket index."""
    match i:
        case 1 | 3 | 5:
            painter.drawImage(
                int(SOCKET_PX - LINK_LENGTH / 2),
                int(row * SOCKET_PX + SOCKET_PX / 2 - LINK_WIDTH / 2),
                link_h,
            )
        case 2:
            painter.drawImage(
                int(SOCKET_PX * 1.5 - LINK_WIDTH / 2),
                int(row * SOCKET_PX - LINK_LENGTH / 2),
                link_v,
            )
        case 4:
            painter.drawImage(
                int(SOCKET_PX / 2 - LINK_WIDTH / 2),
                int(row * SOCKET_PX - LINK_LENGTH / 2),
                link_v,
            )
        case _:
            logger.error('Unexpected socket index %s', i)


def _draw_2width_sockets(
    painter: QPainter,
    socket_groups: List[m_socket.SocketGroup],
    width: int,
) -> Tuple[int, int]:
    """Draws sockets and links for a 2 width item."""
    link_v = QImage(os.path.join(SOCKET_DIR, 'LinkV.png'))
    link_h = QImage(os.path.join(SOCKET_DIR, 'LinkH.png'))

    i = 0
    socket_rows = 0
    socket_cols = 0
    for socket_group in socket_groups:
        for j, socket in enumerate(socket_group):
            socket_img = QImage(SOCKET_FILE.format(socket.name))
            if width == 1:
                painter.drawImage(0, SOCKET_PX * i, socket_img)
                if j > 0:
                    painter.drawImage(16, SOCKET_PX * i - 19, link_v)
                socket_cols = 1
                socket_rows = i + 1
            else:
                assert width == 2
                row = i // 2
                col = i % 2
                if row % 2 == 1:
                    col = 1 - col
                painter.drawImage(SOCKET_PX * col, SOCKET_PX * row, socket_img)
                if j > 0:
                    _draw_2width_links(painter, i, row, link_v, link_h)
                socket_rows = max(row + 1, socket_rows)
                socket_cols = max(col + 1, socket_cols)
            i += 1

    return socket_rows, socket_cols


def property_function(prop_name: str) -> Callable[['Item'], str]:
    """Returns the function that returns a specific property given an item."""

    def func(item: 'Item') -> str:
        item_prop = next((x for x in item.props if x.name == prop_name), None)
        if item_prop is not None:
            val = item_prop.values[0][0]
            assert isinstance(val, str)
            return val
        return ''

    return func


class Item:
    """Class to represent an Item."""

    def __init__(self, item_json: Dict[str, Any], tab: str) -> None:
        """Initializes every field that is needed, given the API JSON of the item."""
        self.name = (
            item_json['typeLine']
            if item_json['name'] == ''
            else item_json['name'] + ', ' + item_json['baseType']
        )

        self.width = item_json.get('w', 1)
        self.height = item_json.get('h', 1)

        self.influences = list(item_json.get('influences', {}).keys())

        self.props = [
            m_property.Property(p['name'], p['values'])
            for p in item_json.get('properties', [])
        ]
        self.reqs = [
            requirement.Requirement(r['name'], r['values'])
            for r in item_json.get('requirements', [])
        ]

        stack_size = item_json.get('stackSize')
        if stack_size and not self.props:
            self.props.append(m_property.Property('Stack Size', [[stack_size, 0]]))

        self.logbook: List[Dict[str, Any]] = item_json.get('logbookMods', [])
        self.implicit = item_json.get('implicitMods', [])
        self.scourge = item_json.get('scourgeMods', [])
        self.utility = item_json.get('utilityMods', [])
        self.fractured = item_json.get('fracturedMods', [])
        self.explicit = item_json.get('explicitMods', [])
        self.crafted = item_json.get('craftedMods', [])
        self.veiled = ['Veiled ' + mod[:-2] for mod in item_json.get('veiledMods', [])]
        self.enchanted = item_json.get('enchantMods', [])
        self.crucible = item_json.get('crucibleMods', [])
        self.cosmetic = item_json.get('cosmeticMods', [])

        self.incubator = item_json.get('incubatedItem')
        self.prophecy = item_json.get('prophecyText')
        self.gem = item_json.get('secDescrText')

        self.split = item_json.get('split', False)
        self.corrupted = item_json.get('corrupted', False)
        self.identified = item_json.get('identified', False)
        self.mirrored = item_json.get('duplicated', False)
        self.fractured_tag = item_json.get('fractured', False)
        self.synthesised = item_json.get('synthesised', False)
        self.searing = item_json.get('searing', False)
        self.tangled = item_json.get('tangled', False)
        self.unmodifiable = item_json.get('unmodifiable', False)

        self.scourged = item_json.get('scourged')

        self.ilvl = item_json.get('ilvl')
        self.rarity = gamedata.RARITIES.get(item_json['frameType'], 'normal')

        sockets = item_json.get('sockets')
        self.socket_groups = m_socket.create_sockets(sockets)

        self.visible = True
        self.tab = tab
        self.tooltip = []

        self.category = self._get_category(item_json)
        self.additional = item_json.get('additionalProperties')

        if self.category in gamedata.GEM_CATEGORIES:
            gen_quality = (
                alt_quality
                for alt_quality in gamedata.ALTERNATE_QUALITIES
                if alt_quality in item_json['typeLine']
            )
            self.gem_quality = next(gen_quality, 'Superior (Default)')
        else:
            self.gem_quality = None

        self.internal_mods: Dict[str, List[float]] = {}

        self.icon = item_json['icon']

        self.file_path = ''
        if (z := re.search(r'\/([^.]+\.png)', self.icon)) is not None:
            paths = z.group().split('/')
            self.file_path = os.path.join(IMAGE_CACHE_DIR, *paths)

        self._wep_props()
        self._arm_props()
        self._sock_props()
        self._req_props()
        self._misc_props()

    def __lt__(self, other: 'Item') -> bool:
        # TODO: deal with tab num, character names
        if self.tab < other.tab:
            return True

        if self.tab > other.tab:
            return False

        return self.name < other.name

    def __str__(self) -> str:
        return self.name

    def _wep_props(self) -> None:
        # Physical damage
        z = re.search(NUM_RANGE_REGEX, property_function('Physical Damage')(self))
        physical_damage = (
            (float(z.group(1)) + float(z.group(2))) / 2.0 if z is not None else 0
        )

        # Chaos damage
        z = re.search(NUM_RANGE_REGEX, property_function('Chaos Damage')(self))
        chaos_damage = (
            (float(z.group(1)) + float(z.group(2))) / 2.0 if z is not None else 0
        )

        # Multiple elements damage
        elemental_damage = 0
        item_prop = next((x for x in self.props if x.name == 'Elemental Damage'), None)
        if item_prop is not None:
            for val in item_prop.values:
                assert isinstance(val[0], str)
                if (z := re.search(NUM_RANGE_REGEX, val[0])) is not None:
                    elemental_damage += (float(z.group(1)) + float(z.group(2))) / 2.0

        # Total damage
        self.damage = physical_damage + chaos_damage + elemental_damage

        # APS
        aps = property_function('Attacks per Second')(self)
        self.aps = float(aps) if aps != '' else None

        # Crit chance
        z = re.search(
            FLAT_PERCENT_REGEX, property_function('Critical Strike Chance')(self)
        )
        self.crit = float(z.group(1)) if z is not None else None

        # Calculate DPS
        self.dps = self.damage * self.aps if self.aps is not None else None
        self.pdps = physical_damage * self.aps if self.aps is not None else None
        self.edps = elemental_damage * self.aps if self.aps is not None else None

    def _arm_props(self) -> None:
        # Defences
        armour = property_function('Armour')(self)
        self.armour = int(armour) if armour else None

        evasion = property_function('Evasion Rating')(self)
        self.evasion = int(evasion) if evasion else None

        energy_shield = property_function('Energy Shield')(self)
        self.energy_shield = int(energy_shield) if energy_shield else None

        ward = property_function('Ward')(self)
        self.ward = int(ward) if ward else None

        # Block
        z = re.search(PERCENT_REGEX, property_function('Chance to Block')(self))
        self.block = int(z.group(1)) if z is not None else None

    def _sock_props(self) -> None:
        self.sockets = [
            socket for socket_group in self.socket_groups for socket in socket_group
        ]
        self.sockets_r = self.sockets.count(m_socket.Socket.R)
        self.sockets_g = self.sockets.count(m_socket.Socket.G)
        self.sockets_w = self.sockets.count(m_socket.Socket.W)
        self.sockets_b = self.sockets.count(m_socket.Socket.B)
        self.num_sockets = len(self.sockets)

        self.num_links = (
            max(len(socket_group) for socket_group in self.socket_groups)
            if self.has_sockets()
            else 0
        )

    def _req_props(self) -> None:
        # fmt: off
        req_level = next((req for req in self.reqs if req.name == 'Level'), None)
        self.req_level = int(req_level.values[0][0]) if req_level is not None else None

        req_str = next((req for req in self.reqs if req.name in ('Strength', 'Str')), None)
        self.req_str = int(req_str.values[0][0]) if req_str is not None else None

        req_dex = next((req for req in self.reqs if req.name in ('Dexterity', 'Dex')), None)
        self.req_dex = int(req_dex.values[0][0]) if req_dex is not None else None

        req_int = next((req for req in self.reqs if req.name in ('Intelligence', 'Int')), None)
        self.req_int = int(req_int.values[0][0]) if req_int is not None else None

        req_class = next((req for req in self.reqs if req.name == 'Class:'), None)
        self.req_class = req_class.values[0][0] if req_class is not None else None
        # fmt: on

    def _misc_props(self) -> None:
        # Pre-formatted properties
        self.quality = property_function('Quality')(self)
        z = re.search(PLUS_PERCENT_REGEX, self.quality)
        self.quality_num = int(z.group(1)) if z is not None else None

        z = re.search(NUMBER_REGEX, property_function('Level')(self))
        self.gem_lvl = int(z.group(1)) if z is not None else None

        # Gem experience
        if self.category in gamedata.GEM_CATEGORIES and self.additional is not None:
            exp = self.additional[0]['values'][0][0]
            index = exp.index('/')
            self.current_exp = int(exp[0:index])
            self.max_exp = int(exp[index + 1 :])
            self.gem_exp = self.current_exp / self.max_exp * 100
        else:
            self.current_exp = None
            self.max_exp = None
            self.gem_exp = None

        self.altart = any(name in self.icon for name in gamedata.ALTART)
        self.crafted_tag = len(self.crafted) > 0
        self.veiled_tag = len(self.veiled) > 0
        self.enchanted_tag = len(self.enchanted) > 0
        self.scourge_tier: int = (
            self.scourged['tier'] if self.scourged is not None else 0
        )
        self.cosmetic_tag = len(self.cosmetic) > 0

    def _get_influence_tooltip(self) -> str:
        icons = list(self.influences)
        if self.veiled_tag:
            icons.append('veiled')
        if self.fractured_tag:
            icons.append('fractured')
        if self.synthesised:
            icons.append('synthesised')
        if self.tangled:
            icons.append('tangled')
        if self.searing:
            icons.append('searing')

        influence_icons = (
            f'<img src="{consts.ITEM_TYPE_SRC}/{infl}.png" />' for infl in icons
        )
        return ''.join(influence_icons)

    def _get_header_tooltip(self) -> str:
        name = util.colorize(self.name.replace(', ', '<br />'), self.rarity)
        return consts.HEADER_TEMPLATE.format(name)

    def _get_prophecy_tooltip(self) -> str:
        return (
            util.colorize(self.prophecy, 'white') if self.prophecy is not None else ''
        )

    def _get_property_tooltip(self) -> str:
        if not self.props:
            return ''

        tooltip: List[str] = []
        for i, item_prop in enumerate(self.props):
            tooltip.append(item_prop.description)
            if i < len(self.props) - 1:
                tooltip.append('<br />')

        return ''.join(tooltip)

    def _get_utility_tooltip(self) -> str:
        mods = _list_mods([ModGroup(self.utility, 'magic')])
        if mods:
            return '<br />' + mods

        return ''

    def _get_expedition_tooltips(self) -> List[str]:
        if not self.logbook:
            return []

        tooltips: List[str] = []
        for area in self.logbook:
            tooltip = [
                util.colorize(area['name'], 'white'),
                util.colorize(area['faction']['name'], 'grey'),
            ]
            for mod in area['mods']:
                tooltip.append(util.colorize(mod, 'magic'))
            tooltips.append('<br />'.join(tooltip))

        return tooltips

    def _get_requirement_tooltip(self) -> str:
        if not self.reqs:
            return ''

        tooltip: List[str] = []
        tooltip.append(util.colorize('Requires', 'grey'))
        for i, req in enumerate(self.reqs):
            if i > 0:
                tooltip.append(util.colorize(',', 'grey'))
            tooltip.append(' ' + req.description)

        return ''.join(tooltip)

    def _get_gem_secondary_tooltip(self) -> str:
        return util.colorize(self.gem, 'gem') if self.gem is not None else ''

    def _get_ilevel_tooltip(self) -> str:
        """For Metamorph samples and Captured beasts."""
        if 'Metamorph' in self.icon or 'BestiaryOrb' in self.icon:
            label = util.colorize('Item Level: ', 'grey')
            assert self.ilvl is not None
            value = util.colorize(self.ilvl, 'white')
            return label + value

        return ''

    def _get_additional_tooltip(self) -> str:
        if self.additional is None:
            return ''

        if self.category in gamedata.GEM_CATEGORIES:
            # Gem experience text
            label = util.colorize('Experience: ', 'grey')
            value = util.colorize(f'{self.current_exp:,}/{self.max_exp:,}', 'white')
            return label + value

        if self.category == 'Sentinel':
            # Sentinel charge text
            lines: List[str] = []
            for prop in self.additional:
                val = prop.get('values')[0]
                lines.append(
                    util.colorize(prop.get('name') + ': ', 'grey')
                    + util.colorize(val[0], util.valnum_to_color(val[1], val[0]))
                )
            return '<br />'.join(lines)

        if self.name == 'Chronicle of Atzoatl':
            # Chronicle of Atzoatl room text
            lines: List[str] = []
            for prop in self.additional:
                if (name := prop.get('name')) != '':
                    lines.append(util.colorize(name, 'grey'))
                else:
                    val = prop.get('values')[0]
                    lines.append(
                        util.colorize(val[0], util.valnum_to_color(val[1], val[0]))
                    )
            return '<br />'.join(lines)

        logger.error(
            'Unexpected additional mods for item %s %s', self.name, self.category
        )
        return ''

    def _get_incubator_tooltip(self) -> str:
        if self.incubator is None:
            return ''

        progress = int(self.incubator['progress'])
        total = int(self.incubator['total'])
        name = self.incubator['name']
        level = self.incubator['level']
        return (
            util.colorize(f'Incubating {name}', 'craft')
            + '<br />'
            + util.colorize(f'{progress:,}/{total:,}', 'white')
            + util.colorize(f' level {level}+ monster kills', 'grey')
        )

    def _get_scourge_tooltip(self) -> str:
        if self.scourge_tier < 1:
            return ''

        return util.colorize(f'Scourged (Tier {self.scourge_tier})', 'scourged')

    def _get_category(self, item_json: Dict[str, Any]) -> str:
        """Returns an item's category based on its other properties."""
        # Gem
        if (support := item_json.get('support')) is not None:
            return 'Support Gem' if support else 'Skill Gem'

        if item_json.get('prophecyText') is not None:
            return 'Prophecy'

        # Property
        if (properties := item_json.get('properties')) is not None:
            cat = properties[0]['name']
            if cat == 'Abyss':
                return 'Abyss Jewel'
            if cat == 'Genus':
                return 'Captured Beast'
            if cat == 'Uses':
                return 'Metamorph Sample'

            if cat in gamedata.COMBO_ITEMS['Category']:
                return cat

        # Special base types
        item_base = item_json['baseType']
        if 'Talisman' in item_base:
            return 'Amulet'
        if 'Lure' in item_base:
            return 'Scarab'
        if item_base == 'Ultimatum Aspect' or 'Piece' in item_base:
            return 'Unique Fragment'
        if item_base in (
            'Primeval Remnant',
            'Primordial Remnant',
            'Engraved Ultimatum',
        ):
            return 'Map'
        if '\'s Crest' in item_base:
            return 'Map Fragment'
        if item_base == 'Simulacrum':  # Avoid conflict with splinter
            return 'Map Fragment'
        if 'Memory' in item_base:
            return 'Memory Line'
        if item_base in (
            'Charged Compass',
            'Fossilised Delirium Orb',  # Conflict: fossil
            'Jeweller\'s Orb',  # Conflict: jewel
            'Tainted Jeweller\'s Orb',  # Conflict: jewel
        ):
            return 'Currency'

        # Fragments
        for frag in gamedata.FRAGMENTS:
            if frag in item_base:
                return 'Map Fragment'

        # From basetype list
        for base_type, search_list in gamedata.BASE_TYPES.items():
            if any(search == item_base for search in search_list):
                return base_type

        # From basetype word
        for cat in gamedata.PARSE_CATEGORIES:
            if cat in item_base:
                return cat

        # Eldritch Invitations
        if 'Invitation' in item_base:
            return 'Map'

        # Chronicle of Atzoatl
        if item_base == 'Chronicle of Atzoatl':
            return 'Map'

        # Rarity
        if self.rarity == 'divination':
            return 'Divination Card'
        if self.rarity == 'currency':
            return 'Currency'
        if self.rarity == 'quest':
            return 'Quest'

        logger.warning('Unknown category %s %s %s', self.name, item_base, self.rarity)
        return ''

    def get_image(self) -> QPixmap:
        """Returns an item's image with sockets and links."""
        image = QImage(self.file_path)
        pixmap = QPixmap(SOCKET_PX * self.width, SOCKET_PX * self.height)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)

        offset_width = (pixmap.width() - image.width()) // 2
        offset_height = (pixmap.height() - image.height()) // 2
        painter.drawImage(offset_width, offset_height, image)

        if self.num_sockets == 0:
            return pixmap

        socket_pixmap = QPixmap(SOCKET_PX * self.width, SOCKET_PX * self.height)
        socket_pixmap.fill(Qt.GlobalColor.transparent)
        socket_painter = QPainter(socket_pixmap)
        socket_rows = 1
        socket_cols = 1

        if self.num_sockets == 1:
            socket_img = QImage(SOCKET_FILE.format(self.sockets[0].name))
            socket_painter.drawImage(0, 0, socket_img)
        else:
            socket_rows, socket_cols = _draw_2width_sockets(
                socket_painter, self.socket_groups, self.width
            )

        socket_painter.end()
        socket_pixmap = socket_pixmap.copy(
            0, 0, SOCKET_PX * socket_cols, SOCKET_PX * socket_rows
        )
        painter.drawPixmap(
            (pixmap.width() - socket_pixmap.width()) // 2,
            (pixmap.height() - socket_pixmap.height()) // 2,
            socket_pixmap,
        )
        painter.end()

        return pixmap

    def get_tooltip(self) -> List[str]:
        """
        Returns a list of strings, with each representing a single section of the entire
        tooltip.
        """
        if self.tooltip:
            return self.tooltip

        self.tooltip = [
            self._get_influence_tooltip(),
            self._get_header_tooltip(),
            self._get_prophecy_tooltip()
            + self._get_property_tooltip()
            + self._get_utility_tooltip(),
        ]
        self.tooltip.extend(self._get_expedition_tooltips())
        self.tooltip.extend(
            (
                self._get_requirement_tooltip(),
                self._get_gem_secondary_tooltip(),
                self._get_ilevel_tooltip(),
                _list_mods([ModGroup(self.enchanted, 'craft')]),
                _list_mods([ModGroup(self.scourge, 'scourged')]),
                _list_mods([ModGroup(self.implicit, 'magic')]),
                _list_mods(
                    [
                        ModGroup(self.fractured, 'currency'),
                        ModGroup(self.explicit, 'magic'),
                        ModGroup(self.veiled, 'grey'),
                        ModGroup(self.crafted, 'craft'),
                    ]
                ),
                _list_tags(
                    [
                        Tag('Split', 'magic', self.split),
                        Tag('Corrupted', 'red', self.corrupted),
                        Tag('Unidentified', 'red', not self.identified),
                        Tag('Mirrored', 'magic', self.mirrored),
                        Tag('Unmodifiable', 'magic', self.unmodifiable),
                    ]
                ),
                _list_mods([ModGroup(self.crucible, 'scourged')]),
                self._get_additional_tooltip(),
                _list_mods([ModGroup(self.cosmetic, 'currency')]),
                self._get_incubator_tooltip(),
                self._get_scourge_tooltip(),
            )
        )
        self.tooltip = [group for group in self.tooltip if len(group) > 0]

        return self.tooltip

    def get_text(self) -> str:
        """Returns text format of item."""
        if not self.tooltip:
            return ''

        # Remove influence icons from tooltip
        tooltip = self.tooltip[1:] if '<img' in self.tooltip[0] else self.tooltip

        # Clean up inline HTML from tooltip
        text = re.sub(BR_REGEX, '\n', '\n'.join(tooltip))
        text = re.sub(CLEAN_REGEX, '', text)
        return text

    def has_sockets(self) -> bool:
        """Returns whether item has sockets."""
        return len(self.socket_groups) > 0
