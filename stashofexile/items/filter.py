"""
Defines Filter class and filter functions for each item filter.
"""
import dataclasses

from typing import Callable, List, Optional, Type, Union

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QIntValidator, QValidator
from PyQt6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLineEdit, QWidget

import gamedata

from items import item
from widgets import editcombo

FilterFunction = Callable[..., bool]
Num = Union[int, float]

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

    def _main_unchecked(self, checked: int) -> None:
        if checked == 0:
            for influence in self.influences:
                influence.setCheckState(Qt.CheckState.Unchecked)

    def _influence_checked(self, checked: int) -> None:
        if checked == 2:
            self.check.setCheckState(Qt.CheckState.Checked)

    def item_match(self, item: item.Item) -> bool:
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
    """

    name: str
    widget: Type[QWidget]
    filter_func: FilterFunction
    validator: Optional[QValidator] = None


@dataclasses.dataclass
class FilterGroup:
    """
    Represents a group of item filters.
    """

    name: str
    filters: List[Filter]


def filter_is_active(widget: QWidget) -> bool:
    """Determines whether a filter is active (based on widget type)."""
    if isinstance(widget, QCheckBox):
        return widget.isChecked()
    if isinstance(widget, QLineEdit):
        return len(widget.text()) > 0
    if isinstance(widget, QComboBox):
        return widget.currentIndex() > 0
    if isinstance(widget, InfluenceFilter):
        return widget.check.isChecked()
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

    if len(bot_str) == 0 and len(top_str) == 0:
        # Filter field is blank
        return True

    if field is None or field == default_val:
        # Field is default value or not set
        return False

    # Field is between two inputs
    bot = conv_func(bot_str) if len(bot_str) > 0 and bot_str != '.' else min_val
    top = conv_func(top_str) if len(top_str) > 0 and top_str != '.' else max_val
    return bot <= field <= top


def _filter_name(item: item.Item, elem: QLineEdit) -> bool:
    """Filter function that uses name."""
    return elem.text().lower() in item.name.lower()


def _filter_category(item: item.Item, elem: QComboBox) -> bool:
    """Filter function that uses category."""
    text = elem.currentText()
    return text == item.category


def _filter_rarity(item: item.Item, elem: QComboBox) -> bool:
    """Filter function that uses rarity."""
    text = elem.currentText()
    if item.rarity == text.lower():
        return True
    if text == 'Any Non-Unique' and item.rarity not in ['unique', 'foil']:
        return True

    return False


def _duo_filt_num(field_str: str, conv_func: Callable[[str], Num]) -> FilterFunction:
    """Generic double QLineEditor filter function."""

    def filt(item: item.Item, elem1: QLineEdit, elem2: QLineEdit) -> bool:
        field = vars(item).get(field_str)
        return field is not None and _between_filter(field, elem1, elem2, conv_func)

    return filt


def _get_filter_ilevel() -> FilterFunction:
    """Returns a filter function that uses item level."""
    return _duo_filt_num('ilvl', int)


def _filter_influences(item: item.Item, elem: InfluenceFilter) -> bool:
    """Filter function that uses influence."""
    return elem.item_match(item)


def _filter_mod(
    item: item.Item, elem: editcombo.EditComboBox, range1: QLineEdit, range2: QLineEdit
) -> bool:
    """Filter function that searches for mods."""
    mod_str = elem.currentText()
    if mod_str == '':
        return True

    return mod_str in item.internal_mods and all(
        _between_filter(value, range1, range2, float)
        for value in item.internal_mods[mod_str]
    )


FILTERS = [
    Filter('Name', QLineEdit, _filter_name),
    Filter('Category', editcombo.EditComboBox, _filter_category),
    Filter('Rarity', editcombo.EditComboBox, _filter_rarity),
    Filter('Damage', QLineEdit, _duo_filt_num('damage', float), DV),
    Filter('Attacks per Second', QLineEdit, _duo_filt_num('aps', float), DV),
    Filter('Critical Chance', QLineEdit, _duo_filt_num('crit', float), DV),
    Filter('Damage per Second', QLineEdit, _duo_filt_num('dps', float), DV),
    Filter('Physical DPS', QLineEdit, _duo_filt_num('pdps', float), DV),
    Filter('Elemental DPS', QLineEdit, _duo_filt_num('edps', float), DV),
    Filter('Quality', QLineEdit, _duo_filt_num('quality_num', int), IV),
    Filter('Item Level', QLineEdit, _get_filter_ilevel(), IV),
    Filter('Influenced', InfluenceFilter, _filter_influences),
]

MOD_FILTERS = [Filter('', editcombo.EditComboBox, _filter_mod) for _ in range(5)]