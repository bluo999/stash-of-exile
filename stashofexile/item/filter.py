"""
Defines Filter class and filter functions for each item filter.
"""

from typing import Callable, Optional, Type, Union
from dataclasses import dataclass
from PyQt6.QtGui import QDoubleValidator, QIntValidator, QValidator

from PyQt6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QWidget

from item.item import Item

FilterFunction = Callable[..., bool]
Num = Union[int, float]

MIN_VAL = 0
MAX_VAL = 100000
IV = QIntValidator()
DV = QDoubleValidator()


@dataclass
class Filter:
    """
    Represents an item filter.

    Fields:
        name: Label name.
        widget: Widget type of filter.
        filterFunc: Filter function.
        numericOnly: Whether to restrict QLineEdit to numbers only.
    """

    name: str
    widget: Type[QWidget]
    filter_func: FilterFunction
    validator: Optional[QValidator] = None


def filter_is_active(widget: QWidget) -> bool:
    """Determines whether a filter is active (based on widget type)."""
    if isinstance(widget, QCheckBox):
        return widget.isChecked()
    if isinstance(widget, QLineEdit):
        return len(widget.text()) > 0
    if isinstance(widget, QComboBox):
        return widget.currentIndex() > 0
    return False


def _filter_name(item: Item, elem: QLineEdit) -> bool:
    """Filter function that uses name."""
    return elem.text().lower() in item.name.lower()


def _filter_category(item: Item, elem: QComboBox) -> bool:
    """Filter function that uses category."""
    text = elem.currentText()
    return text == item.category


def _filter_rarity(item: Item, elem: QComboBox) -> bool:
    """Filter function that uses rarity."""
    text = elem.currentText()
    if item.rarity == text.lower():
        return True
    if text == 'Any Non-Unique' and item.rarity not in ['unique', 'foil']:
        return True

    return False


def _duo_filt_num(
    field_str: str,
    conv_func: Callable[[str], Num],
    min_val: Num = MIN_VAL,
    max_val: Num = MAX_VAL,
    default_val: Num = 0,
) -> FilterFunction:
    """
    Generic double QLineEditor filter function.

    Checks Noneness and whether the field is between the two input values.

    Args:
        field_str (str): Field of item JSON to get value from.
        conv_func (Callable[[str], Num]): Function to convert string to number (int
        or float).
        min_val (Num, optional): [Min value of processed field]. Defaults to MIN_VAL.
        max_val (Num, optional): [Max value of processed field]. Defaults to MAX_VAL.
        default_val (Num, optional): [Default value of processed fifeld]. Defaults to 0.

    Returns:
        FilterFunction: [The filter function]
    """

    def filt(item: Item, elem1: QLineEdit, elem2: QLineEdit) -> bool:
        bot_str = elem1.text()
        top_str = elem2.text()

        if len(bot_str) == 0 and len(top_str) == 0:
            # Filter field is blank
            return True

        field = vars(item).get(field_str)
        if field is None or field == default_val:
            # Field is default value or not set
            return False

        # Field is between two inputs
        bot = conv_func(bot_str) if len(bot_str) > 0 and bot_str != '.' else min_val
        top = conv_func(top_str) if len(top_str) > 0 and top_str != '.' else max_val
        return bot <= field <= top

    return filt


def _get_filter_ilevel() -> FilterFunction:
    """Returns a filter function that uses item level."""
    return _duo_filt_num('ilvl', int, max_val=100)


def _filter_influences(item: Item, elem: QCheckBox) -> bool:
    """Filter function that uses influence."""
    assert elem.isChecked()
    return len(item.influences) > 0


def _filter_mod(item: Item, elem: QLineEdit) -> bool:
    """Filter function that searches for mods."""
    search = elem.text().lower()
    return any(
        any(search in mod.lower() for mod in mod_group)
        for mod_group in (item.fractured, item.explicit, item.crafted)
    )


FILTERS = [
    Filter('Name', QLineEdit, _filter_name),
    Filter('Category', QComboBox, _filter_category),
    Filter('Rarity', QComboBox, _filter_rarity),
    Filter('Damage', QLineEdit, _duo_filt_num('damage', float), DV),
    Filter('Attacks per Second', QLineEdit, _duo_filt_num('aps', float), DV),
    Filter('Critical Chance', QLineEdit, _duo_filt_num('crit', float), DV),
    Filter('Damage per Second', QLineEdit, _duo_filt_num('dps', float), DV),
    Filter('Physical DPS', QLineEdit, _duo_filt_num('pdps', float), DV),
    Filter('Elemental DPS', QLineEdit, _duo_filt_num('edps', float), DV),
    Filter('Quality', QLineEdit, _duo_filt_num('qualityNum', int), IV),
    Filter('Item Level', QLineEdit, _get_filter_ilevel(), IV),
    Filter('Influenced', QCheckBox, _filter_influences),
    Filter('Mod', QLineEdit, _filter_mod),
    Filter('Mod', QLineEdit, _filter_mod),
    Filter('Mod', QLineEdit, _filter_mod),
]
