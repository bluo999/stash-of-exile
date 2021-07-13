from typing import Callable, Type
from dataclasses import dataclass

from PyQt6.QtWidgets import QComboBox, QLineEdit, QWidget

from item import Item

FilterFunction = Callable[[QWidget, Item], bool]


@dataclass
class Filter:
    name: str
    widget: Type[QWidget]
    filterFunc: FilterFunction


def _filterName(elem: QWidget, item: Item) -> bool:
    """Filter function that uses name."""
    assert isinstance(elem, QLineEdit)
    return elem.text().lower() in item.name.lower()


def _filterCategory(elem: QWidget, item: Item) -> bool:
    """Filter function that uses category."""
    assert isinstance(elem, QComboBox)
    text = elem.currentText()
    return text == 'Any' or text == item.category


def _filterRarity(elem: QWidget, item: Item) -> bool:
    """Filter function that uses rarity."""
    assert isinstance(elem, QComboBox)
    if elem.currentText() == 'Any':
        return True
    if item.rarity == elem.currentText().lower():
        return True
    if elem.currentText() == 'Any Non-Unique' and item.rarity not in ['unique', 'foil']:
        return True

    return False


FILTERS = [
    Filter('Name', QLineEdit, _filterName),
    Filter('Category', QComboBox, _filterCategory),
    Filter('Rarity', QComboBox, _filterRarity),
]
