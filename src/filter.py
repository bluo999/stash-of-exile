import re

from typing import Any, Callable, Type, Union
from dataclasses import dataclass

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
    numericOnly: bool


def _filterName(item: Item, elem: QLineEdit) -> bool:
    """Filter function that uses name."""
    return elem.text().lower() in item.name.lower()


def _filterCategory(item: Item, elem: QWidget) -> bool:
    """Filter function that uses category."""
    text = elem.currentText()
    return text == 'Any' or text == item.category


def _filterRarity(item: Item, elem: QComboBox) -> bool:
    """Filter function that uses rarity."""
    if elem.currentText() == 'Any':
        return True
    if item.rarity == elem.currentText().lower():
        return True
    if elem.currentText() == 'Any Non-Unique' and item.rarity not in ['unique', 'foil']:
        return True

    return False


def _filterDuoNumeric(
    fieldStr: str,
    defaultVal: Num,
    minVal: Num,
    maxVal: Num,
    convFunc: Callable[[str], Num],
    procFunc: Callable[[Any], Num],
) -> FilterFunction:
    """Returns a generic double QLineEdit filter function that checks Noneness
    and whether the field is between the two input values.
    
    Args:
        fieldStr: Field of item JSON to get value from.
        defaultVal: Default value of processed field.
        minVal: Minimum value of processed field.
        maxVal: Maximum value of processed field.
        convFunc: Function to convert string to number (int or float).
        procFunc: Function to process field.
    """

    def filter(item: Item, elem1: QLineEdit, elem2: QLineEdit) -> bool:
        botStr = elem1.text()
        topStr = elem2.text()
        field: Num = procFunc(vars(item).get(fieldStr))
        if field is None:
            return False
        elif field == defaultVal and (len(botStr) > 0 or len(topStr) > 0):
            return False
        else:
            bot = convFunc(botStr) if botStr.isnumeric() else minVal
            top = convFunc(topStr) if topStr.isnumeric() else maxVal
            return bot <= field <= top

    return filter


def _getFilterQuality() -> FilterFunction:
    """Returns a filter function that uses quality."""
    defaultVal = 0

    def procFunc(ilvlStr: str) -> int:
        z = re.search(r'\+(\d+)%', ilvlStr)
        if z is not None:
            return int(z.group(1))
        else:
            return defaultVal

    return _filterDuoNumeric('quality', defaultVal, 0, 100, int, procFunc)


def _getFilterItemLevel() -> FilterFunction:
    """Returns a filter function that uses item level."""
    return _filterDuoNumeric('ilvl', 0, 0, 100, int, lambda x: x)


def _filterInfluences(item: Item, elem: QCheckBox) -> bool:
    """Filter function that uses influence."""
    return (not elem.isChecked()) or len(item.influences) > 0


FILTERS = [
    Filter('Name', QLineEdit, _filterName, False),
    Filter('Category', QComboBox, _filterCategory, False),
    Filter('Rarity', QComboBox, _filterRarity, False),
    Filter('Quality', QLineEdit, _getFilterQuality(), True),
    Filter('Item Level', QLineEdit, _getFilterItemLevel(), True),
    Filter('Influenced', QCheckBox, _filterInfluences, False),
]
