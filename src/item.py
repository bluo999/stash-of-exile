from typing import Any, Dict, List, Tuple

from consts import HEADER_TEMPLATE, SPAN_TEMPLATE, COLORS
from gameData import CATEGORIES, FRAGMENTS, RARITIES
from requirement import Requirement
from property import Property


def _propertyFunction(prop: str):
    def f(item: 'Item') -> str:
        filtProps = [x for x in item.properties if x.name == prop]
        if len(filtProps) != 0:
            return filtProps[0].values[0][0]
        return ''

    return f


def _frameTypeToRarity(frameType: int) -> str:
    return RARITIES.get(frameType, 'normal')


def _listMods(mods: List[str], color: str) -> str:
    if len(mods) == 0:
        return ''

    # Split mods with \n
    for i in range(len(mods)):
        while '\n' in mods[i]:
            index = mods[i].index('\n')
            mods.insert(i + 1, mods[i][index + 1 :])
            mods[i] = mods[i][:index]

    # Add mods on separate lines
    text = ''
    for i, mod in enumerate(mods):
        text += SPAN_TEMPLATE.format(COLORS[color], mod)
        if i < len(mods) - 1:
            text += '<br />'

    return text


def _listMods(modLists: List[Tuple[List[str], str]]) -> str:
    if len(modLists[0]) == 0:
        return ""

    # Split mods with \n
    for (mods, _) in modLists:
        for i in range(len(mods)):
            while '\n' in mods[i]:
                index = mods[i].index('\n')
                mods.insert(i + 1, mods[i][index + 1 :])
                mods[i] = mods[i][:index]

    # Add mods on separate lines
    text = ''
    for i, (mods, color) in enumerate(modLists):
        for j, mod in enumerate(mods):
            text += SPAN_TEMPLATE.format(COLORS[color], mod)
            if i < len(modLists) - 1 or j < len(mods) - 1:
                text += '<br />'

    return text


def _listTag(tag: bool, tagStr: str, color: str) -> str:
    if tag:
        return f'<p>{SPAN_TEMPLATE.format(COLORS[color] ,tagStr)}</p>'
    return ''


class Item:
    def __init__(self, itemJson: Dict[str, Any], tabNum: int):
        self.name = (
            itemJson['typeLine']
            if itemJson['name'] == ''
            else itemJson['name'] + ', ' + itemJson['baseType']
        )

        self.influences = list(itemJson.get('influences', {}).keys())

        self.properties = [Property(p) for p in itemJson.get('properties', [])]
        self.requirements = [Requirement(r) for r in itemJson.get('requirements', [])]

        self.implicit = itemJson.get('implicitMods', [])
        self.utility = itemJson.get('utilityMods', [])
        self.fractured = itemJson.get('fracturedMods', [])
        self.explicit = itemJson.get('explicitMods', [])
        self.crafted = itemJson.get('craftedMods', [])
        self.enchanted = itemJson.get('enchantMods', [])
        self.cosmetic = itemJson.get('cosmeticMods', [])

        self.incubator = itemJson.get('incubatedItem')
        self.prophecy = itemJson.get('prophecyText')
        self.gem = itemJson.get('secDescrText')
        self.experience = itemJson.get('additionalProperties')

        self.split = itemJson.get('split', False)
        self.corrupted = itemJson.get('corrupted', False)
        self.unidentified = not itemJson.get('identified', False)
        self.mirrored = itemJson.get('mirrored', False)
        self.fracturedTag = itemJson.get('fractured', False)

        self.ilvl = itemJson.get("ilvl")
        self.rarity = _frameTypeToRarity(itemJson['frameType'])

        self.sockets = itemJson.get("sockets")

        self.visible = True
        self.tabNum = tabNum

        self.tooltip = []

        self.setCategory(itemJson)

        self.icon = itemJson["icon"]
        self.filePath = ''
        self.downloaded = False

    def __lt__(self, other):
        """Default ordering for Items."""
        if self.tabNum < other.tabNum:
            return True
        elif self.tabNum > other.tabNum:
            return False

        return self.name < other.name

    def __str__(self):
        return self.name

    def setCategory(self, itemJson: Dict[str, Any]):
        # From basetype
        categories = [
            'Quiver',
            'Trinket',
            'Cluster Jewel',
            'Flask',
            'Map',
            'Maven\'s Invitation',
            'Scarab',
            'Watchstone',
            'Leaguestone',
            'Fossil',
            'Resonator',
            'Incubator',
        ]
        for cat in categories:
            if cat in itemJson['baseType']:
                self.category = cat
                return

        # Fragments
        for frag in FRAGMENTS:
            if frag in itemJson['baseType']:
                self.category = 'Map Fragment'

        # Rarity
        if self.rarity == 'divination':
            self.category = 'Divination Card'
            return
        if self.rarity == 'currency':
            self.category = 'Currency'
            return
        categories.append('Currency')

        # Gem
        if itemJson.get('support') is not None:
            self.category = 'Support Gem' if itemJson['support'] else 'Skill Gem'
            return

        # Property
        if itemJson.get('properties') is not None:
            cat = itemJson['properties'][0]['name']
            if cat == 'Abyss':
                self.category = 'Abyss Jewel'
                return

            if cat in CATEGORIES:
                self.category = cat
                return

        # Search in icon name
        categories = [cat for cat in CATEGORIES if cat not in categories]
        for cat in categories:
            # Remove spaces
            if cat.replace(' ', '') in itemJson['icon']:
                self.category = cat
                return

        if 'Hat' in itemJson['icon']:
            self.category = 'Helmet'
            return
        if 'Metamorph' in itemJson['icon']:
            self.category = 'Metamorph Sample'
            return
        if 'BestiaryOrb' in itemJson['icon']:
            self.category = 'Captured Beast'
            return

    def getTooltip(self) -> List[str]:
        if len(self.tooltip) > 0:
            return self.tooltip

        self.tooltip = []

        # Image
        self.tooltip.append(f'<img src="{self.filePath}" />')

        # Header
        header = SPAN_TEMPLATE.format(
            COLORS[self.rarity], self.name.replace(', ', '<br />')
        )
        self.tooltip.append(HEADER_TEMPLATE.format(header))

        # Description
        tooltip = ''

        # Prophecy text
        if self.prophecy is not None:
            tooltip += f'{SPAN_TEMPLATE.format(COLORS["white"], self.prophecy)}'

        # Properties
        if len(self.properties) > 0:
            for i, prop in enumerate(self.properties):
                tooltip += prop.description()
                if i < len(self.properties) - 1:
                    tooltip += '<br />'

        # Utility mods (flasks)
        mods = _listMods([(self.utility, 'magic')])
        if len(mods) > 0:
            tooltip += '<br />' + mods

        if len(tooltip) > 0:
            self.tooltip.append(tooltip)
            tooltip = ''

        # Requirements
        if len(self.requirements) > 0:
            tooltip += SPAN_TEMPLATE.format('grey', 'Requires')
            for i, req in enumerate(self.requirements):
                if i > 0:
                    tooltip += ','
                tooltip += ' ' + req.description()
            print(tooltip)
            self.tooltip.append(tooltip)
            tooltip = ''

        # Gem secondary description
        if self.gem is not None:
            tooltip += f'{SPAN_TEMPLATE.format(COLORS["gem"], self.gem)}'
            self.tooltip.append(tooltip)
            tooltip = ''

        # Metamorph, itemized beast item level
        if 'Metamorph' in self.icon or 'BestiaryOrb' in self.icon:
            tooltip += SPAN_TEMPLATE.format(
                COLORS['grey'], 'Item Level: '
            ) + SPAN_TEMPLATE.format(COLORS['white'], self.ilvl)
            self.tooltip.append(tooltip)
            tooltip = ''

        # Mods
        mods = _listMods([(self.enchanted, 'craft')])
        tooltip += mods
        if len(mods) != 0:
            self.tooltip.append(tooltip)
            tooltip = ''

        mods = _listMods([(self.implicit, 'magic')])
        tooltip += mods
        if len(mods) != 0:
            self.tooltip.append(tooltip)
            tooltip = ''

        mods = _listMods(
            [
                (self.fractured, 'currency'),
                (self.explicit, 'magic'),
                (self.crafted, 'craft'),
            ]
        )
        tooltip += mods
        if len(mods) != 0:
            self.tooltip.append(tooltip)
            tooltip = ''

        # Tags
        tooltip += _listTag(self.split, 'Split', 'magic')
        tooltip += _listTag(self.corrupted, 'Corrupted', 'red')
        tooltip += _listTag(self.unidentified, 'Unidentified', 'red')
        tooltip += _listTag(self.mirrored, 'Mirrored', 'magic')

        # Gem experience

        # Incubator info

        # Skin transfer

        if len(tooltip) > 0:
            self.tooltip.append(f'<center>{tooltip}</center>')

        return self.tooltip

    PROPERTY_FUNCS = {
        'Name': lambda item: item.name,
        'Tab': lambda item: str(item.tabNum),
        'Stack': _propertyFunction('Stack Size'),
        'iLvl': lambda item: str(item.ilvl) if item.ilvl != 0 else '',
        'Quality': _propertyFunction('Quality'),
        'Split': lambda item: 'Split' if item.split else '',
        'Corr': lambda item: 'Corr' if item.corrupted else '',
        'Mir': lambda item: 'Mir' if item.mirrored else '',
        'Unid': lambda item: 'Unid' if item.unidentified else '',
        'Bench': lambda item: 'Bench' if item.crafted else '',
        'Ench': lambda item: 'Ench' if item.enchanted else '',
        'Frac': lambda item: 'Frac' if item.fractured else '',
    }
