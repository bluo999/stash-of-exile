"""
Defines the custom table used to disable items.
"""

from typing import Callable, Dict, List

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QObject, QVariant, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QTableView, QWidget
from consts import COLORS
from filter import FILTERS, filter_is_active

import log

from api import _get_time_ms
from item import Item, property_function

logger = log.get_logger(__name__)


def _influence_func(item: 'Item') -> str:
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
        'Tab': lambda item: str(item.tab),
        'Stack': property_function('Stack Size'),
        'iLvl': lambda item: str(item.ilvl) if item.ilvl != 0 else '',
        'Quality': lambda item: item.quality,
        'Split': lambda item: 'Split' if item.split else '',
        'Corr': lambda item: 'Corr' if item.corrupted else '',
        'Mir': lambda item: 'Mir' if item.mirrored else '',
        'Unid': lambda item: 'Unid' if item.unidentified else '',
        'Bench': lambda item: 'Bench' if item.crafted else '',
        'Ench': lambda item: 'Ench' if item.enchanted else '',
        'Frac': lambda item: 'Frac' if item.fractured else '',
        'Influence': _influence_func,
    }

    def __init__(self, table_view: QTableView, parent: QObject) -> None:
        """Initialize the table model."""
        QAbstractTableModel.__init__(self, parent)
        self.items: List[Item] = []
        self.current_items: List[Item] = []
        self.filter_widgets: List[List[QWidget]] = []
        self.property_funcs = [func for _, func in TableModel.PROPERTY_FUNCS.items()]
        self.headers = list(TableModel.PROPERTY_FUNCS.keys())
        self.table_view = table_view

    def rowCount(self, _parent: QModelIndex) -> int:  # pylint: disable=invalid-name
        """Returns the current number of current rows (excluding filtered)."""
        return len(self.current_items)

    def columnCount(self, _parent: QModelIndex) -> int:  # pylint: disable=invalid-name
        """Returns the number of columns / properties."""
        return len(self.property_funcs)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        """Returns the data stored under the given
        role for the item referred to by the index."""
        row = index.row()
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return self.property_funcs[column](self.current_items[row])

        if role == Qt.ItemDataRole.ForegroundRole:
            if column == 0:
                # Color item name based on rarity
                rarity = self.current_items[row].rarity
                return QColor(COLORS[rarity])
            return QColor(COLORS['white'])

        if role == Qt.ItemDataRole.BackgroundRole:
            return QColor(COLORS['darkgrey'])

        return None

    def headerData(  # pylint: disable=invalid-name
        self, section: int, orientation: Qt.Orientation, role: int
    ) -> object:
        """Returns the data for the given role and section
        in the header with the specified orientation."""
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return QVariant(self.headers[section])

        return None

    def insert_items(self, items: List[Item]) -> None:
        """Inserts a list of items into the table."""
        self.beginInsertRows(QModelIndex(), 0, len(items) - 1)
        self.items.extend(items)
        self.current_items.extend(items)
        self.endInsertRows()

    def set_filter_widgets(self, filter_widgets: List[List[QWidget]]) -> None:
        """Sets the filter widgets for the table."""
        self.filter_widgets = filter_widgets

    def apply_filters(
        self, index: int = 1, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder
    ) -> None:
        """Apply a filter based on several search parameters,
        updating the current items and layout."""
        # Previously selected item
        selection = self.table_view.selectedIndexes()
        selected_item = (
            self.current_items[selection[0].row()] if len(selection) > 0 else None
        )

        # Items that pass every filter
        prev_time = _get_time_ms()
        active_filters = [
            (filter, filter_widgets)
            for filter, filter_widgets in zip(FILTERS, self.filter_widgets)
            if any(filter_is_active(widget) for widget in filter_widgets)
        ]
        self.current_items = [
            item
            for item in self.items
            if all(
                filter.filter_func(item, *filter_widgets)
                for (filter, filter_widgets) in active_filters
            )
        ]
        logger.debug('Filtering took %sms', _get_time_ms() - prev_time)

        key = list(TableModel.PROPERTY_FUNCS.keys())[index]
        sort_func = TableModel.PROPERTY_FUNCS[key]
        self.current_items.sort(
            key=sort_func, reverse=order == Qt.SortOrder.DescendingOrder
        )

        # Clear selection if the item is filtered
        if selected_item is not None:
            if selected_item in self.current_items:
                self.table_view.selectRow(self.current_items.index(selected_item))
            else:
                self.table_view.clearSelection()

        self.layoutChanged.emit()
