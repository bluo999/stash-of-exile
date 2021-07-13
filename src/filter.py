import re

from typing import Any, Callable, List, Type, Union
from dataclasses import dataclass

from PyQt6.QtWidgets import QComboBox, QLineEdit, QWidget

from item import Item, propertyFunction
from property import Property

FilterFunction = Callable[[Item, QWidget], bool]
DuoFilterFunction = Callable[[Item, QWidget, QWidget], bool]
Num = Union[int, float]


@dataclass
class Filter:
    name: str
    widget: Type[QWidget]
    filterFunc: FilterFunction
    numericOnly: bool


@dataclass
class DuoFilter:
    name: str
    widget: Type[QWidget]
    filterFunc: DuoFilterFunction
    numericOnly: bool


def _filterName(item: Item, elem: QWidget) -> bool:
    """Filter function that uses name."""
    assert isinstance(elem, QLineEdit)
    return elem.text().lower() in item.name.lower()


def _filterCategory(item: Item, elem: QWidget) -> bool:
    """Filter function that uses category."""
    assert isinstance(elem, QComboBox)
    text = elem.currentText()
    return text == 'Any' or text == item.category


def _filterRarity(item: Item, elem: QWidget) -> bool:
    """Filter function that uses rarity."""
    assert isinstance(elem, QComboBox)
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
) -> DuoFilterFunction:
    """Returns a generic duo filter function that checks Noneness
    and whether the field is between the two QLineEdit values."""

    def filter(item: Item, elem: QWidget, elem2: QWidget) -> bool:
        assert isinstance(elem, QLineEdit)
        assert isinstance(elem2, QLineEdit)
        botStr = elem.text()
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


def _filterQuality(item: Item, elem: QWidget, elem2: QWidget) -> bool:
    """Filter function that uses quality."""
    defaultVal = 0

    def procFunc(props: List[Property]) -> int:
        ilvlStr = propertyFunction('Quality')(item)
        z = re.search(r'\+(\d+)%', ilvlStr)
        if z is not None:
            return int(z.group(1))
        else:
            return defaultVal

    return _filterDuoNumeric('properties', defaultVal, 0, 100, int, procFunc)(
        item, elem, elem2
    )


def _filterItemLevel(item: Item, elem: QWidget, elem2: QWidget) -> bool:
    """Filter function that uses item level."""
    return _filterDuoNumeric('ilvl', 0, 0, 100, int, lambda x: x)(item, elem, elem2)


FILTERS = [
    Filter('Name', QLineEdit, _filterName, False),
    Filter('Category', QComboBox, _filterCategory, False),
    Filter('Rarity', QComboBox, _filterRarity, False),
    DuoFilter('Quality', QLineEdit, _filterQuality, True),
    DuoFilter('Item Level', QLineEdit, _filterItemLevel, True),
]
