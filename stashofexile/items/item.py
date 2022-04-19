"""
Defines parsing of the item API and converting into a local object.
"""

import os
import re

from typing import Any, Callable, Dict, List, NamedTuple

from stashofexile import consts, gamedata, log
from stashofexile.items import property, requirement

PLUS_PERCENT_REGEX = r'\+(\d+)%'  # +x%
PERCENT_REGEX = r'(\d+)%'
FLAT_PERCENT_REGEX = r'([0-9]{1,2}\.\d{2})%'  # xx.xx%
NUM_RANGE_REGEX = r'(\d+)-(\d+)'  # x-x

IMAGE_CACHE_DIR = os.path.join('image_cache')

logger = log.get_logger(__name__)


class ModGroup(NamedTuple):
    """Represents a mod group."""

    mods: List[str]
    color: str


class Tag(NamedTuple):
    """Represents a tag."""

    name: str
    color: str
    active: bool


def _list_mods(mod_groups: List[ModGroup]) -> str:
    """
    Given a list of mod lists, returns a single complete line separated, colored
    string of mods.
    """
    # Get rid of any empty mod list
    filt_mod_lists = [
        (mod_group.mods, mod_group.color) for mod_group in mod_groups if mod_group.mods
    ]

    if not filt_mod_lists:
        return ''

    # Split mods with \n
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

    # Add mods on separate lines
    text: List[str] = []
    for i, (mods, color) in enumerate(filt_mod_lists):
        for j, mod in enumerate(mods):
            text.append(consts.SPAN_TEMPLATE.format(consts.COLORS[color], mod))
            if i < len(filt_mod_lists) - 1 or j < len(mods) - 1:
                text.append('<br />')

    return ''.join(text)


def _list_tags(tag_info: List[Tag]) -> str:
    """
    Given a list of tags, returns a single complete line separate, colored string of
    tags.
    """
    # Get rid of inactive tags then format them
    formatted_tags = [
        consts.SPAN_TEMPLATE.format(consts.COLORS[tag.color], tag.name)
        for tag in tag_info
        if tag.active
    ]

    # Add tags on separate lines
    text: List[str] = []
    for i, tag in enumerate(formatted_tags):
        text.append(tag)
        if i < len(formatted_tags) - 1:
            text.append('<br />')

    return ''.join(text)


def property_function(prop_name: str) -> Callable[['Item'], str]:
    """Returns the function that returns a specific property given an item."""

    def func(item: 'Item') -> str:
        prop = next((x for x in item.props if x.name == prop_name), None)
        if prop is not None:
            val = prop.values[0][0]
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

        self.influences = list(item_json.get('influences', {}).keys())

        self.props = [
            property.Property({'name': p['name'], 'vals': p['values']})
            for p in item_json.get('properties', [])
        ]
        self.reqs = [
            requirement.Requirement({'name': r['name'], 'vals': r['values']})
            for r in item_json.get('requirements', [])
        ]

        self.implicit = item_json.get('implicitMods', [])
        self.utility = item_json.get('utilityMods', [])
        self.fractured = item_json.get('fracturedMods', [])
        self.explicit = item_json.get('explicitMods', [])
        self.crafted = item_json.get('craftedMods', [])
        self.enchanted = item_json.get('enchantMods', [])
        self.cosmetic = item_json.get('cosmeticMods', [])

        self.incubator = item_json.get('incubatedItem')
        self.prophecy = item_json.get('prophecyText')
        self.gem = item_json.get('secDescrText')

        self.split = item_json.get('split', False)
        self.corrupted = item_json.get('corrupted', False)
        self.unidentified = not item_json.get('identified', False)
        self.mirrored = item_json.get('mirrored', False)
        self.fractured_tag = item_json.get('fractured', False)

        self.ilvl = item_json.get('ilvl')
        self.rarity = gamedata.RARITIES.get(item_json['frameType'], 'normal')

        self.sockets = item_json.get('sockets')

        self.visible = True
        self.tab = tab
        self.tooltip = []

        self.category = self.get_category(item_json)
        self.experience = (
            item_json.get('additionalProperties')
            if self.category in {'Skill Gem', 'Support Gem'}
            else None
        )

        self.internal_mods: Dict[str, List[float]] = {}

        self.icon = item_json['icon']

        self.file_path = ''
        if (z := re.search(r'\/([^.]+\.png)', self.icon)) is not None:
            paths = z.group().split('/')
            # Some generated file names are the same for different images:
            # if 'gen' in paths:
            #     index = paths.index('gen')
            #     paths = paths[0: index + 1] + paths[-1:]
            self.file_path = os.path.join(IMAGE_CACHE_DIR, *paths)

        self._wep_props()
        self._arm_props()
        self._req_props()

    def __lt__(self, other: 'Item') -> bool:
        """Default ordering for Items."""
        # TODO: deal with tab num, character names
        if self.tab < other.tab:
            return True

        if self.tab > other.tab:
            return False

        return self.name < other.name

    def __str__(self) -> str:
        return self.name

    def get_category(self, item_json: Dict[str, Any]) -> str:
        """
        Determines and returns an item's category based on its other
        properties.
        """
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

        item_base = item_json['baseType']

        # Special base types
        if 'Talisman' in item_base:
            return 'Amulet'
        if 'Lure' in item_base:
            return 'Scarab'
        if 'Piece' in item_base:
            return 'Unique Fragment'
        if 'Crest' in item_base:
            return 'Map Fragment'
        if item_base == 'Simulacrum':  # Avoid conflict with splinter
            return 'Map Fragment'
        if item_base == 'Charged Compass':
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

        # Rarity
        if self.rarity == 'divination':
            return 'Divination Card'
        if self.rarity == 'currency':
            return 'Currency'

        logger.warning('Unknown category %s %s %s', self.name, item_base, self.rarity)
        return ''

    def get_tooltip(self) -> List[str]:
        """
        Returns a list of strings, with each representing a single section of the
        entire tooltip.
        """
        if self.tooltip:
            return self.tooltip

        mods = _list_mods(
            [
                ModGroup(self.fractured, 'currency'),
                ModGroup(self.explicit, 'magic'),
                ModGroup(self.crafted, 'craft'),
            ]
        )
        tags = _list_tags(
            [
                Tag('Split', 'magic', self.split),
                Tag('Corrupted', 'red', self.corrupted),
                Tag('Unidentified', 'red', self.unidentified),
                Tag('Mirrored', 'magic', self.mirrored),
            ]
        )
        self.tooltip = [
            # Image
            f'<img src="{self.file_path}" />',
            # Item name (header)
            self._get_header_tooltip(),
            # Prophecy, properties, utility mods
            self._get_prophecy_tooltip()
            + self._get_property_tooltip()
            + self._get_utility_tooltip(),
            # Requirements
            self._get_requirement_tooltip(),
            # Gem secondary description
            self._get_gem_secondary_tooltip(),
            # Item level (metamorph, bestiary orb)
            self._get_ilevel_tooltip(),
            # Mods
            _list_mods([ModGroup(self.enchanted, 'craft')]),
            _list_mods([ModGroup(self.implicit, 'magic')]),
            # Mods and Tags
            f'{mods}<br />{tags}' if mods and tags else mods + tags,
            # Gem experience
            self._get_gem_exp_tooltip(),
            # Incubator info
            self._get_incubator_tooltip(),
            # Skin transfers
            _list_mods([ModGroup(self.cosmetic, 'currency')]),
        ]
        self.tooltip = [group for group in self.tooltip if len(group) > 0]

        return self.tooltip

    def _wep_props(self) -> None:
        """Populates weapon properties of item from base stats (e.g. pdps)."""
        # Pre-formatted properties
        self.quality = property_function('Quality')(self)
        if (z := re.search(PLUS_PERCENT_REGEX, self.quality)) is not None:
            self.quality_num = int(z.group(1))

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
        prop = next((x for x in self.props if x.name == 'Elemental Damage'), None)
        if prop is not None:
            for val in prop.values:
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
        """Populates armour properties of item from base stats (e.g. evasion)."""
        armour = property_function('Armour')(self)
        self.armour = int(armour) if armour else None

        evasion = property_function('Evasion')(self)
        self.evasion = int(evasion) if evasion else None

        es = property_function('Energy Shield')(self)
        self.es = int(es) if es else None

        ward = property_function('Ward')(self)
        self.ward = int(ward) if ward else None

        # Block
        z = re.search(PERCENT_REGEX, property_function('Chance to Block')(self))
        self.block = int(z.group(1)) if z is not None else None

    def _req_props(self) -> None:
        """Populates requirement properties."""
        req_level = next((req for req in self.reqs if req.name == 'Level'), None)
        self.req_level = int(req_level.values[0][0]) if req_level is not None else None

        req_str = next(
            (req for req in self.reqs if req.name in ('Strength', 'Str')), None
        )
        self.req_str = int(req_str.values[0][0]) if req_str is not None else None

        req_dex = next(
            (req for req in self.reqs if req.name in ('Dexterity', 'Dex')), None
        )
        self.req_dex = int(req_dex.values[0][0]) if req_dex is not None else None

        req_int = next(
            (req for req in self.reqs if req.name in ('Intelligence', 'Int')), None
        )
        self.req_int = int(req_int.values[0][0]) if req_int is not None else None

        req_class = next((req for req in self.reqs if req.name == 'Class:'), None)
        self.req_class = req_class.values[0][0] if req_class is not None else None

    def _get_header_tooltip(self) -> str:
        """Returns the header tooltip, including influence icons and a colorized name."""
        influence_icons = [
            f'<img src="assets/{infl}.png" />' for infl in self.influences
        ]
        name = consts.SPAN_TEMPLATE.format(
            consts.COLORS[self.rarity], self.name.replace(', ', '<br />')
        )

        return ''.join(influence_icons) + consts.HEADER_TEMPLATE.format(name)

    def _get_prophecy_tooltip(self) -> str:
        """Returns the colorized prophecy tooltip."""
        return (
            consts.SPAN_TEMPLATE.format(consts.COLORS['white'], self.prophecy)
            if self.prophecy is not None
            else ''
        )

    def _get_property_tooltip(self) -> str:
        """Returns the colorized, line separated properties tooltip."""
        tooltip: List[str] = []
        if self.props:
            for i, prop in enumerate(self.props):
                tooltip.append(prop.description)
                if i < len(self.props) - 1:
                    tooltip.append('<br />')

        return ''.join(tooltip)

    def _get_utility_tooltip(self) -> str:
        """Returns the colorized, line separated utility mods tooltip."""
        mods = _list_mods([ModGroup(self.utility, 'magic')])
        if mods:
            return '<br />' + mods

        return ''

    def _get_requirement_tooltip(self) -> str:
        """Returns the colorized, line separated requirements tooltip."""
        tooltip: List[str] = []
        if self.reqs:
            tooltip.append(consts.SPAN_TEMPLATE.format('grey', 'Requires'))
            for i, req in enumerate(self.reqs):
                if i > 0:
                    tooltip.append(',')
                tooltip.append(' ' + req.description)

        return ''.join(tooltip)

    def _get_gem_secondary_tooltip(self) -> str:
        """Returns the colorized, line separated gem description tooltip."""
        return (
            consts.SPAN_TEMPLATE.format(consts.COLORS['gem'], self.gem)
            if self.gem is not None
            else ''
        )

    def _get_ilevel_tooltip(self) -> str:
        """
        Returns the colorized item level tooltip for organs and bestiary orbs.
        """
        if 'Metamorph' in self.icon or 'BestiaryOrb' in self.icon:
            label = consts.SPAN_TEMPLATE.format(consts.COLORS['grey'], 'Item Level: ')
            value = consts.SPAN_TEMPLATE.format(consts.COLORS['white'], self.ilvl)
            return label + value

        return ''

    def _get_gem_exp_tooltip(self) -> str:
        """Returns the colorized gem experience tooltip."""
        if self.experience is not None:
            exp = self.experience[0]['values'][0][0]
            index = exp.index('/')
            current_exp = int(exp[0:index])
            max_exp = int(exp[index + 1 :])
            label = consts.SPAN_TEMPLATE.format(consts.COLORS['grey'], 'Experience: ')
            value = consts.SPAN_TEMPLATE.format(
                consts.COLORS['white'], f'{current_exp:,}/{max_exp:,}'
            )
            return label + value

        return ''

    def _get_incubator_tooltip(self) -> str:
        """Returns the colorized, line separated incubator tooltip."""
        if self.incubator is not None:
            progress = int(self.incubator['progress'])
            total = int(self.incubator['total'])
            name = self.incubator['name']
            level = self.incubator['level']
            return (
                consts.SPAN_TEMPLATE.format(
                    consts.COLORS['craft'], f'Incubating {name}'
                )
                + '<br />'
                + consts.SPAN_TEMPLATE.format(
                    consts.COLORS['white'], f'{progress:,}/{total:,}'
                )
                + consts.SPAN_TEMPLATE.format(
                    consts.COLORS['grey'], f' level {level}+ monster kills'
                )
            )

        return ''
