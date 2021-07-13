from typing import Callable, Dict, List

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QObject, QVariant, Qt
from PyQt6.QtGui import QColor
from consts import COLORS

from item import Item


def _propertyFunction(prop: str) -> Callable[['Item'], str]:
    """Returns the function that returns a specific property given an item."""

    def f(item: 'Item') -> str:
        filtProps = [x for x in item.properties if x.name == prop]
        if len(filtProps) != 0:
            val = filtProps[0].values[0][0]
            assert isinstance(val, str)
            return val
        return ''

    return f


def _influenceFunction(item: 'Item') -> str:
    """Given an item return an influence string, which is a list of
    capital letters for each influence."""
    ret = ''
    for infl in item.influences:
        ret += infl[0]
    return ret.upper()


class TableModel(QAbstractTableModel):
    """Custom table model used to store, filter, and sort Items."""

    # Keys: name of the header
    # Values: function that computes the value
    PROPERTY_FUNCS: Dict[str, Callable[[Item], str]] = {
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
        'Influence': _influenceFunction,
    }

    def __init__(self, parent: QObject) -> None:
        """Initialize the table model."""
        QAbstractTableModel.__init__(self, parent)
        self.items: List[Item] = []
        self.currentItems: List[Item] = []
        self.propertyFuncs = [func for (_, func) in TableModel.PROPERTY_FUNCS.items()]
        self.headers = list(TableModel.PROPERTY_FUNCS.keys())
        self.setFilter()

    def rowCount(self, parent: QModelIndex) -> int:
        """Returns the current number of current rows (excluding filtered)."""
        return len(self.currentItems)

    def columnCount(self, parent: QModelIndex) -> int:
        """Returns the number of columns / properties."""
        return len(self.propertyFuncs)

    def insertItems(self, items: List[Item]) -> None:
        """Inserts a list of items into the table."""
        self.beginInsertRows(QModelIndex(), 0, len(items))
        self.items.extend(items)
        self.currentItems.extend(items)
        self.endInsertRows()

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        """Returns the data stored under the given
        role for the item referred to by the index."""
        row = index.row()
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return self.propertyFuncs[column](self.currentItems[row])
        elif role == Qt.ItemDataRole.ForegroundRole:
            if column == 0:
                rarity = self.currentItems[row].rarity
                return QColor(COLORS[rarity])
            else:
                return QColor(COLORS['white'])
        elif role == Qt.ItemDataRole.BackgroundRole:
            return QColor(COLORS['darkgrey'])

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int
    ) -> object:
        """Returns the data for the given role and section
        in the header with the specified orientation."""
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return QVariant(self.headers[section])

    def setFilter(self, searchText: str = "") -> None:
        """Apply a filter based on several search parameters,
        updating the current items and layout."""
        self.currentItems = [
            item for item in self.items if searchText.lower() in item.name.lower()
        ]
        # pyright: reportFunctionMemberAccess=false
        self.layoutChanged.emit()
