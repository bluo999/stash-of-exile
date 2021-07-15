from typing import Any, Callable, Dict, List, Tuple

from consts import HEADER_TEMPLATE, SPAN_TEMPLATE, COLORS
from gameData import COMBO_ITEMS, FRAGMENTS, RARITIES
from requirement import Requirement
from property import Property


def propertyFunction(prop: str) -> Callable[['Item'], str]:
    """Returns the function that returns a specific property given an item."""

    def f(item: 'Item') -> str:
        filtProps = [x for x in item.properties if x.name == prop]
        if len(filtProps) != 0:
            val = filtProps[0].values[0][0]
            assert isinstance(val, str)
            return val
        return ''

    return f


def _listMods(modLists: List[Tuple[List[str], str]]) -> str:
    """
    Given a list of mod lists, returns a single complete
    line separated, colored string of mods.
    """
    # Get rid of any empty mod list
    filtModLists = [(mods, color) for (mods, color) in modLists if len(mods) > 0]

    if len(filtModLists) == 0:
        return ''

    # Split mods with \n
    for mods, _ in filtModLists:
        i = 0
        length = len(mods)
        while i < length:
            while '\n' in mods[i]:
                index = mods[i].index('\n')
                mods.insert(i + 1, mods[i][index + 1 :])
                mods[i] = mods[i][:index]
                length += 1
            i += 1

    # Add mods on separate lines
    text: str = ''
    for i, (mods, color) in enumerate(filtModLists):
        for j, mod in enumerate(mods):
            text += SPAN_TEMPLATE.format(COLORS[color], mod)
            if i < len(filtModLists) - 1 or j < len(mods) - 1:
                text += '<br />'

    return text


def _listTags(tagInfo: List[Tuple[bool, str, str]]) -> str:
    """
    Given a list of tags, returns a single complete
    line separate, colored string of tags.
    """
    # Get rid of inactive tags
    formattedTags = [
        SPAN_TEMPLATE.format(COLORS[color], tagStr)
        for (tagActive, tagStr, color) in tagInfo
        if tagActive
    ]

    text = ''
    for i, tag in enumerate(formattedTags):
        text += tag
        if i < len(formattedTags) - 1:
            text += '<br />'

    return text


class Item:
    """Class to represent an Item."""

    def __init__(self, itemJson: Dict[str, Any], tabNum: int) -> None:
        """Initializes every field that is needed, given the API JSON of the item."""
        self.name = (
            itemJson['typeLine']
            if itemJson['name'] == ''
            else itemJson['name'] + ', ' + itemJson['baseType']
        )

        self.influences = list(itemJson.get('influences', {}).keys())

        self.properties = [
            Property({'name': p['name'], 'vals': p['values']})
            for p in itemJson.get('properties', [])
        ]
        self.requirements = [
            Requirement({'name': r['name'], 'vals': r['values']})
            for r in itemJson.get('requirements', [])
        ]

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

        self.ilvl = itemJson.get('ilvl')
        self.rarity = RARITIES.get(itemJson['frameType'], 'normal')

        self.sockets = itemJson.get("sockets")

        self.visible = True
        self.tabNum = tabNum

        self.tooltip = []

        self.category = self.getCategory(itemJson)

        self.icon = itemJson['icon']
        self.filePath = ''
        self.downloaded = False

        self.quality = propertyFunction('Quality')(self)

    def __lt__(self, other: 'Item') -> bool:
        """Default ordering for Items."""
        if self.tabNum < other.tabNum:
            return True
        elif self.tabNum > other.tabNum:
            return False

        return self.name < other.name

    def __str__(self) -> str:
        return self.name

    def getCategory(self, itemJson: Dict[str, Any]) -> str:
        """Determines and returns an item's category
        based on its other properties."""
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
                return cat

        # Fragments
        for frag in FRAGMENTS:
            if frag in itemJson['baseType']:
                return 'Map Fragment'

        # Rarity
        if self.rarity == 'divination':
            return 'Divination Card'
        if self.rarity == 'currency':
            return 'Currency'

        # Add currency to ignore when searching in icon name
        categories.append('Currency')

        # Gem
        if itemJson.get('support') is not None:
            return 'Support Gem' if itemJson['support'] else 'Skill Gem'

        # Property
        if itemJson.get('properties') is not None:
            cat = itemJson['properties'][0]['name']
            if cat == 'Abyss':
                return 'Abyss Jewel'

            if cat in COMBO_ITEMS['Category']:
                return cat

        # Search in icon name
        categories = [cat for cat in COMBO_ITEMS['Category'] if cat not in categories]
        for cat in categories:
            # Remove spaces
            if cat.replace(' ', '') in itemJson['icon']:
                return cat

        # Alternate names in icon name
        if 'Hat' in itemJson['icon']:
            return 'Helmet'
        if 'Metamorph' in itemJson['icon']:
            return 'Metamorph Sample'
        if 'BestiaryOrb' in itemJson['icon']:
            return 'Captured Beast'

        # TODO: add exception
        return ''

    def getTooltip(self) -> List[str]:
        """Returns a list of strings, with each representing
        a single section of the entire tooltip."""
        if len(self.tooltip) > 0:
            return self.tooltip

        mods = _listMods(
            [
                (self.fractured, 'currency'),
                (self.explicit, 'magic'),
                (self.crafted, 'craft'),
            ]
        )
        tags = _listTags(
            [
                (self.split, 'Split', 'magic'),
                (self.corrupted, 'Corrupted', 'red'),
                (self.unidentified, 'Unidentified', 'red'),
                (self.mirrored, 'Mirrored', 'magic'),
            ]
        )
        self.tooltip = [
            # Image
            f'<img src="{self.filePath}" />',
            # Item name (header)
            self.getHeaderTooltip(),
            # Prophecy, properties, utility mods
            self.getProphecyTooltip()
            + self.getPropertyTooltip()
            + self.getUtilityTooltip(),
            # Requirements
            self.getRequirementTooltip(),
            # Gem secondary description
            self.getGemSecondaryTooltip(),
            # Item level (metamorph, bestiary orb)
            self.getItemLevelTooltip(),
            # Mods
            _listMods([(self.enchanted, 'craft')]),
            _listMods([(self.implicit, 'magic')]),
            # Mods and Tags
            f'{mods}<br />{tags}' if len(mods) > 0 and len(tags) > 0 else mods + tags,
            # Gem experience
            self.getGemExperienceTooltip(),
            # Incubator info
            self.getIncubatorTooltip(),
            # Skin transfers
            _listMods([(self.cosmetic, 'currency')]),
        ]
        self.tooltip = [group for group in self.tooltip if len(group) > 0]

        return self.tooltip

    def getHeaderTooltip(self) -> str:
        """Returns the header tooltip, including
        influence icons and a colorized name."""
        influence_icons = ''
        for infl in self.influences:
            influence_icons += f'<img src="../assets/{infl}.png" />'

        name = SPAN_TEMPLATE.format(
            COLORS[self.rarity], self.name.replace(', ', '<br />')
        )

        return influence_icons + HEADER_TEMPLATE.format(name)

    def getProphecyTooltip(self) -> str:
        """Returns the colorized prophecy tooltip."""
        if self.prophecy is not None:
            return SPAN_TEMPLATE.format(COLORS['white'], self.prophecy)

        return ''

    def getPropertyTooltip(self) -> str:
        """Returns the colorized, line separated properties tooltip."""
        tooltip = ''
        if len(self.properties) > 0:
            for i, prop in enumerate(self.properties):
                tooltip += prop.description()
                if i < len(self.properties) - 1:
                    tooltip += '<br />'

        return tooltip

    def getUtilityTooltip(self) -> str:
        """Returns the colorized, line separated utility mods tooltip."""
        mods = _listMods([(self.utility, 'magic')])
        if len(mods) > 0:
            return '<br />' + mods

        return ''

    def getRequirementTooltip(self) -> str:
        """Returns the colorized, line separated requirements tooltip."""
        tooltip = ''
        if len(self.requirements) > 0:
            tooltip += SPAN_TEMPLATE.format('grey', 'Requires')
            for i, req in enumerate(self.requirements):
                if i > 0:
                    tooltip += ','
                tooltip += ' ' + req.description()

        return tooltip

    def getGemSecondaryTooltip(self) -> str:
        """Returns the colorized, line separated gem description tooltip."""
        if self.gem is not None:
            return SPAN_TEMPLATE.format(COLORS['gem'], self.gem)

        return ''

    def getItemLevelTooltip(self) -> str:
        """Returns the colorized item level tooltip
        for organs and bestiary orbs."""
        if 'Metamorph' in self.icon or 'BestiaryOrb' in self.icon:
            label = SPAN_TEMPLATE.format(COLORS['grey'], 'Item Level: ')
            value = SPAN_TEMPLATE.format(COLORS['white'], self.ilvl)
            return label + value

        return ''

    def getGemExperienceTooltip(self) -> str:
        """Returns the colorized gem experience tooltip."""
        if self.experience is not None:
            exp = self.experience[0]['values'][0][0]
            index = exp.index('/')
            currentExp = int(exp[0:index])
            maxExp = int(exp[index + 1 :])
            label = SPAN_TEMPLATE.format(COLORS['grey'], 'Experience: ')
            value = SPAN_TEMPLATE.format(COLORS['white'], f'{currentExp:,}/{maxExp:,}')
            return label + value

        return ''

    def getIncubatorTooltip(self) -> str:
        """Returns the colorized, line separated incubator tooltip."""
        if self.incubator is not None:
            progress = int(self.incubator['progress'])
            total = int(self.incubator['total'])
            name = self.incubator['name']
            level = self.incubator['level']
            return (
                SPAN_TEMPLATE.format(COLORS['craft'], f'Incubating {name}')
                + '<br />'
                + SPAN_TEMPLATE.format(COLORS['white'], f'{progress:,}/{total:,}')
                + SPAN_TEMPLATE.format(COLORS['grey'], f' level {level}+ monster kills')
            )

        return ''
