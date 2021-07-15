from typing import Callable, Dict, List

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QObject, QVariant, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QTableView, QWidget
from consts import COLORS
from filter import FILTERS

from item import Item, propertyFunction


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
        'Stack': propertyFunction('Stack Size'),
        'iLvl': lambda item: str(item.ilvl) if item.ilvl != 0 else '',
        'Quality': lambda item: item.quality,
        'Split': lambda item: 'Split' if item.split else '',
        'Corr': lambda item: 'Corr' if item.corrupted else '',
        'Mir': lambda item: 'Mir' if item.mirrored else '',
        'Unid': lambda item: 'Unid' if item.unidentified else '',
        'Bench': lambda item: 'Bench' if item.crafted else '',
        'Ench': lambda item: 'Ench' if item.enchanted else '',
        'Frac': lambda item: 'Frac' if item.fractured else '',
        'Influence': _influenceFunction,
    }

    def __init__(self, tableView: QTableView, parent: QObject) -> None:
        """Initialize the table model."""
        QAbstractTableModel.__init__(self, parent)
        self.items: List[Item] = []
        self.currentItems: List[Item] = []
        self.propertyFuncs = [func for (_, func) in TableModel.PROPERTY_FUNCS.items()]
        self.headers = list(TableModel.PROPERTY_FUNCS.keys())
        self.tableView = tableView

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

    def setWidgets(self, widgets: List[List[QWidget]]) -> None:
        self.widgets = widgets

    def applyFilters(self) -> None:
        """Apply a filter based on several search parameters,
        updating the current items and layout."""
        self.currentItems = [
            item
            for item in self.items
            if all(
                filter.filterFunc(item, *widgets)
                for (filter, widgets) in zip(FILTERS, self.widgets)
            )
        ]

        self.tableView.clearSelection()

        # pyright: reportFunctionMemberAccess=false
        self.layoutChanged.emit()
