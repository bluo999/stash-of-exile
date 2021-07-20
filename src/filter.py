import re

from typing import Any, Callable, Type, Union
from dataclasses import dataclass
from PyQt6.QtGui import QDoubleValidator, QIntValidator, QValidator

from PyQt6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QWidget

from item import Item

FilterFunction = Callable[..., bool]
Num = Union[int, float]


@dataclass
class Filter:
    """Class to represent an item filter.
    
    Args:
        name: Label name.
        widget: Widget type of filter.
        filterFunc: Filter function.
        numericOnly: Whether to restrict QLineEdit to numbers only.
    """

    name: str
    widget: Type[QWidget]
    filterFunc: FilterFunction
    validator: Union[QValidator, None]

    MIN_VAL = 0
    MAX_VAL = 100000
    IV = QIntValidator()
    DV = QDoubleValidator()


def _filterName(item: Item, elem: QLineEdit) -> bool:
    """Filter function that uses name."""
    return elem.text().lower() in item.name.lower()


def _filterCategory(item: Item, elem: QWidget) -> bool:
    """Filter function that uses category."""
    text = elem.currentText()
    return text == 'Any' or text == item.category


def _filterRarity(item: Item, elem: QComboBox) -> bool:
    """Filter function that uses rarity."""
    text = elem.currentText()
    if text == 'Any':
        return True
    if item.rarity == text.lower():
        return True
    if text == 'Any Non-Unique' and item.rarity not in ['unique', 'foil']:
        return True

    return False


def _duoFiltNum(
    fieldStr: str,
    convFunc: Callable[[str], Num],
    minVal: Num = Filter.MIN_VAL,
    maxVal: Num = Filter.MAX_VAL,
    defaultVal: Num = 0,
) -> FilterFunction:
    """Returns a generic double QLineEdit filter function that checks Noneness
    and whether the field is between the two input values.
    
    Args:
        fieldStr: Field of item JSON to get value from.
        defaultVal: Default value of processed field.
        minVal: Minimum value of processed field.
        maxVal: Maximum value of processed field.
        convFunc: Function to convert string to number (int or float).
    """

    def filter(item: Item, elem1: QLineEdit, elem2: QLineEdit) -> bool:
        botStr = elem1.text()
        topStr = elem2.text()

        if len(botStr) == 0 and len(topStr) == 0:
            # Filter field is blank
            return True

        field = vars(item).get(fieldStr)
        if field is None or field == defaultVal:
            # Field is default value or not set
            return False
        else:
            # Field is between two inputs
            bot = convFunc(botStr) if len(botStr) > 0 and botStr != '.' else minVal
            top = convFunc(topStr) if len(topStr) > 0 and topStr != '.' else maxVal
            return bot <= field <= top

    return filter


def _getFilterItemLevel() -> FilterFunction:
    """Returns a filter function that uses item level."""
    return _duoFiltNum('ilvl', int, maxVal=100)


def _filterInfluences(item: Item, elem: QCheckBox) -> bool:
    """Filter function that uses influence."""
    return (not elem.isChecked()) or len(item.influences) > 0


FILTERS = [
    Filter('Name', QLineEdit, _filterName, None),
    Filter('Category', QComboBox, _filterCategory, None),
    Filter('Rarity', QComboBox, _filterRarity, None),
    Filter('Damage', QLineEdit, _duoFiltNum('damage', float), Filter.DV),
    Filter('Attacks per Second', QLineEdit, _duoFiltNum('aps', float), Filter.DV),
    Filter('Critical Chance', QLineEdit, _duoFiltNum('crit', float), Filter.DV),
    Filter('Damage per Second', QLineEdit, _duoFiltNum('dps', float), Filter.DV),
    Filter('Physical DPS', QLineEdit, _duoFiltNum('pdps', float), Filter.DV),
    Filter('Elemental DPS', QLineEdit, _duoFiltNum('edps', float), Filter.DV),
    Filter('Quality', QLineEdit, _duoFiltNum('qualityNum', int), Filter.IV),
    Filter('Item Level', QLineEdit, _getFilterItemLevel(), Filter.IV),
    Filter('Influenced', QCheckBox, _filterInfluences, None),
]
