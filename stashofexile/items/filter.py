"""
Defines Filter class and filter functions for each item filter.
"""
import dataclasses

from typing import Callable, List, Optional, Type

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QIntValidator, QValidator
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QWidget,
)

from stashofexile import gamedata
from stashofexile.items import item as m_item
from stashofexile.widgets import editcombo

FilterFunction = Callable[..., bool]
Num = int | float

MIN_VAL = -100000
MAX_VAL = 100000
IV = QIntValidator()
DV = QDoubleValidator()


class InfluenceFilter(QWidget):
    """Widget that includes 7 QCheckBoxes for influence filtering."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        hlayout = QHBoxLayout(self)
        self.check = QCheckBox()
        self.check.stateChanged.connect(self._main_unchecked)
        hlayout.addWidget(self.check)
        self.influences: List[QCheckBox] = []
        for _ in range(6):
            influence = QCheckBox()
            influence.stateChanged.connect(self._influence_checked)
            hlayout.addWidget(influence)
            self.influences.append(influence)

    def __repr__(self) -> str:
        if not self.check.isChecked():
            return 'off'

        values = []
        for widget, influence in zip(self.influences, gamedata.Influences):
            if widget.isChecked():
                values.append(influence)

        text = ' '.join(values)
        if text == '':
            return 'on'

        return text

    def _main_unchecked(self, checked: int) -> None:
        if checked == 0:
            for influence in self.influences:
                influence.setCheckState(Qt.CheckState.Unchecked)

    def _influence_checked(self, checked: int) -> None:
        if checked == 2:
            self.check.setCheckState(Qt.CheckState.Checked)

    def item_match(self, item: m_item.Item) -> bool:
        """Returns whether an item conforms to the filter's selection."""
        assert self.check.isChecked()
        return len(item.influences) > 0 and all(
            (not widget.isChecked()) or (influence in item.influences)
            for widget, influence in zip(self.influences, gamedata.Influences)
        )

    def connect(self, func: Callable) -> None:
        """Connect subwidgets to apply filter on state change."""
        self.check.stateChanged.connect(func)
        for influence in self.influences:
            influence.stateChanged.connect(func)


@dataclasses.dataclass
class Filter:
    """
    Represents an item filter.

    Fields:
        name (str): Label name.
        widget (Type[QWidget]): Widget type of filter.
        filter_func (FilterFunction): Filter function.
        validator (QValidator, Optional): Field validator.
        widgets (List[QWidget], Optional): List of widgets.
    """

    name: str
    widget_type: Type[QWidget]
    filter_func: FilterFunction
    validator: Optional[QValidator] = None
    widgets: List[QWidget] = dataclasses.field(default_factory=list)

    def __repr__(self) -> str:
        values: List[str] = []
        for widget in self.widgets:
            match widget:
                case QCheckBox():
                    values.append(str(widget.isChecked()))
                case QLineEdit():
                    values.append(widget.text())
                case QComboBox():
                    values.append(widget.currentText())
                case InfluenceFilter():
                    values.append(repr(widget))
        info = ' '.join(values)

        return f'{self.name}: {info}'


@dataclasses.dataclass
class FilterGroup:
    """
    Represents a group of item filters.
    """

    name: str
    filters: List[Filter]
    start_active: bool = True
    group_box: Optional[QGroupBox] = None


def filter_is_active(widget: QWidget) -> bool:
    """Determines whether a filter is active (based on widget type)."""
    match widget:
        case QCheckBox():
            return widget.isChecked()
        case QLineEdit():
            return len(widget.text()) > 0
        case QComboBox():
            return widget.currentIndex() > 0
        case InfluenceFilter():
            return widget.check.isChecked()
        case _:
            return False


def _between_filter(  # pylint: disable=too-many-arguments
    field: Num,
    elem1: QLineEdit,
    elem2: QLineEdit,
    conv_func: Callable[[str], Num],
    min_val: Num = MIN_VAL,
    max_val: Num = MAX_VAL,
    default_val: Num = 0,
):
    """
    Returns a function that checks whether the field is between the two given
    filters.

    Args:
        field ([type]): Field of item JSON to get value from.
        elem1 (QLineEdit): Widget of lower value
        elem2 (QLineEdit): Widget of upper value
        conv_func (Callable[[str], Num]): Function to convert string to number (int
        or float).
        min_val (Num, optional): [Min value of field]. Defaults to MIN_VAL.
        max_val (Num, optional): [Max value of field]. Defaults to MAX_VAL.
        default_val (Num, optional): [Default value of field]. Defaults to 0.

    Returns:
        FilterFunction: [The filter function]
    """
    bot_str = elem1.text()
    top_str = elem2.text()

    if not bot_str and not top_str:
        # Filter field is blank
        return True

    if field is None or field == default_val:
        # Field is default value or not set
        return False

    # Field is between two inputs
    bot = conv_func(bot_str) if bot_str and bot_str != '.' else min_val
    top = conv_func(top_str) if top_str and top_str != '.' else max_val
    return bot <= field <= top


def _filter_name(item: m_item.Item, elem: QLineEdit) -> bool:
    """Filter function that uses name."""
    return elem.text().lower() in item.name.lower()


def _filter_category(item: m_item.Item, elem: QComboBox) -> bool:
    """Filter function that uses category."""
    text = elem.currentText()
    return text == item.category


def _filter_rarity(item: m_item.Item, elem: QComboBox) -> bool:
    """Filter function that uses rarity."""
    text = elem.currentText()
    if item.rarity == text.lower():
        return True
    if text == 'Any Non-Unique' and item.rarity not in ['unique', 'foil']:
        return True

    return False


def _filter_class(item: m_item.Item, elem: QComboBox) -> bool:
    """Filter function that uses character class."""
    text = elem.currentText()
    return text == item.req_class


def _duo(
    prop: Callable[[m_item.Item], Optional[Num]], conv_func: Callable[[str], Num]
) -> FilterFunction:
    """Generic double QLineEditor filter function."""

    def filt(item: m_item.Item, elem1: QLineEdit, elem2: QLineEdit) -> bool:
        field = prop(item)
        return field is not None and _between_filter(field, elem1, elem2, conv_func)

    return filt


def _bool(prop: Callable[[m_item.Item], bool]) -> FilterFunction:
    """Generic boolean filter function."""

    def filt(item: m_item.Item, elem: QComboBox) -> bool:
        field = prop(item)
        text = elem.currentText()
        return text == '' or (text == 'Yes') == field

    return filt


def _filter_gem_quality(item: m_item.Item, elem: QComboBox) -> bool:
    """Filter function that uses gem quality type."""
    text = elem.currentText()
    if item.gem_quality == text:
        return True

    alternates = ('Anomalous', 'Divergent', 'Phantsmal')
    if text == 'Any Alternate' and item.gem_quality in alternates:
        return True

    return False


def _filter_influences(item: m_item.Item, elem: InfluenceFilter) -> bool:
    """Filter function that uses influence."""
    return elem.item_match(item)


def _filter_mod(
    item: m_item.Item, elem: editcombo.ECBox, range1: QLineEdit, range2: QLineEdit
) -> bool:
    """Filter function that searches for mods."""
    mod_str = elem.currentText()
    if mod_str == '':
        return True

    return mod_str in item.internal_mods and all(
        _between_filter(value, range1, range2, float)
        for value in item.internal_mods[mod_str]
    )


FILTERS: List[Filter | FilterGroup] = [
    Filter('Name', QLineEdit, _filter_name),
    Filter('Category', editcombo.ECBox, _filter_category),
    Filter('Rarity', editcombo.ECBox, _filter_rarity),
    FilterGroup(
        'Weapon Filters',
        [
            Filter('Damage', QLineEdit, _duo(lambda i: i.damage, float), DV),
            Filter('Attacks per Second', QLineEdit, _duo(lambda i: i.aps, float), DV),
            Filter('Critical Chance', QLineEdit, _duo(lambda i: i.crit, float), DV),
            Filter('Damage per Second', QLineEdit, _duo(lambda i: i.dps, float), DV),
            Filter('Physical DPS', QLineEdit, _duo(lambda i: i.pdps, float), DV),
            Filter('Elemental DPS', QLineEdit, _duo(lambda i: i.edps, float), DV),
        ],
    ),
    FilterGroup(
        'Armour Filters',
        [
            Filter('Armour', QLineEdit, _duo(lambda i: i.armour, int), IV),
            Filter('Evasion', QLineEdit, _duo(lambda i: i.evasion, int), IV),
            Filter(
                'Energy Shield', QLineEdit, _duo(lambda i: i.energy_shield, int), IV
            ),
            Filter('Ward', QLineEdit, _duo(lambda i: i.ward, int), IV),
            Filter('Block', QLineEdit, _duo(lambda i: i.block, int), IV),
        ],
    ),
    FilterGroup(
        'Requirements',
        [
            Filter('Level', QLineEdit, _duo(lambda i: i.req_level, int), IV),
            Filter('Strength', QLineEdit, _duo(lambda i: i.req_str, int), IV),
            Filter('Dexterity', QLineEdit, _duo(lambda i: i.req_dex, int), IV),
            Filter('Intelligence', QLineEdit, _duo(lambda i: i.req_int, int), IV),
            Filter('Character Class', editcombo.ECBox, _filter_class),
        ],
        start_active=False,
    ),
    FilterGroup(
        'Miscellaneous',
        [
            Filter('Quality', QLineEdit, _duo(lambda i: i.quality_num, int), IV),
            Filter('Item Level', QLineEdit, _duo(lambda i: i.ilvl, int), IV),
            Filter('Gem Level', QLineEdit, _duo(lambda i: i.gem_lvl, int), IV),
            Filter('Gem Experience %', QLineEdit, _duo(lambda i: i.gem_exp, float), DV),
            Filter('Gem Quality Type', editcombo.ECBox, _filter_gem_quality),
            Filter('Fractured', editcombo.BoolECBox, _bool(lambda i: i.fractured_tag)),
            Filter('Synthesised', editcombo.BoolECBox, _bool(lambda i: i.synthesised)),
            Filter('Searing Exarch', editcombo.BoolECBox, _bool(lambda i: i.searing)),
            Filter('Eater of Worlds', editcombo.BoolECBox, _bool(lambda i: i.tangled)),
            Filter('Alternate Art', editcombo.BoolECBox, _bool(lambda i: i.altart)),
            Filter('Identified', editcombo.BoolECBox, _bool(lambda i: i.identified)),
            Filter('Corrupted', editcombo.BoolECBox, _bool(lambda i: i.corrupted)),
            Filter('Mirrored', editcombo.BoolECBox, _bool(lambda i: i.mirrored)),
            Filter('Split', editcombo.BoolECBox, _bool(lambda i: i.split)),
            Filter('Crafted', editcombo.BoolECBox, _bool(lambda i: i.crafted_tag)),
            Filter('Veiled', editcombo.BoolECBox, _bool(lambda i: i.veiled_tag)),
            Filter('Enchanted', editcombo.BoolECBox, _bool(lambda i: i.enchanted_tag)),
            Filter('Influenced', InfluenceFilter, _filter_influences),
        ],
    ),
]

MOD_FILTERS = [Filter('', editcombo.ECBox, _filter_mod) for _ in range(5)]
