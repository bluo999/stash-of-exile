"""
Defines the custom table used to disable items.
"""

from typing import Callable, Dict, List

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QObject, QVariant, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QTableView

from stashofexile import consts, log
from stashofexile.items import filter as m_filter
from stashofexile.items import item as m_item
from stashofexile.threads import ratelimiting

logger = log.get_logger(__name__)


def _influence_func(item: m_item.Item) -> str:
    """
    Returns an influence string (list of capital letters for each influence) given an
    item.
    """
    influences = [infl[0].upper() for infl in item.influences]
    return ''.join(influences)


class TableModel(QAbstractTableModel):
    """Custom table model used to store, filter, and sort m_item.Items."""

    # Keys: name of the header
    # Values: function that computes the value
    PROPERTY_FUNCS: Dict[str, Callable[[m_item.Item], str]] = {
        'Name': lambda item: item.name,
        'Tab': lambda item: str(item.tab),
        'Stack': m_item.property_function('Stack Size'),
        'iLvl': lambda item: str(item.ilvl) if item.ilvl != 0 else '',
        'Level': m_item.property_function('Level'),
        'Quality': lambda item: item.quality,
        'Split': lambda item: 'Split' if item.split else '',
        'Corr': lambda item: 'Corr' if item.corrupted else '',
        'Mir': lambda item: 'Mir' if item.mirrored else '',
        'Unid': lambda item: 'Unid' if not item.identified else '',
        'Bench': lambda item: 'Bench' if item.crafted else '',
        'Ench': lambda item: 'Ench' if item.enchanted else '',
        'Frac': lambda item: 'Frac' if item.fractured else '',
        'Influence': _influence_func,
    }

    def __init__(self, table_view: QTableView, parent: QObject) -> None:
        super().__init__(parent)
        self.items: List[m_item.Item] = []
        self.current_items: List[m_item.Item] = []
        self.property_funcs = [func for _, func in TableModel.PROPERTY_FUNCS.items()]
        self.headers = list(TableModel.PROPERTY_FUNCS.keys())
        self.table_view = table_view

    def rowCount(  # pylint: disable=invalid-name,unused-argument
        self, parent: QModelIndex
    ) -> int:
        """Returns the current number of current rows (excluding filtered)."""
        return len(self.current_items)

    def columnCount(  # pylint: disable=invalid-name,unused-argument
        self, parent: QModelIndex
    ) -> int:
        """Returns the number of columns / properties."""
        return len(self.property_funcs)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        """
        Returns the data stored under the given role for the item referred to by the
        index.
        """
        row = index.row()
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return self.property_funcs[column](self.current_items[row])

        if role == Qt.ItemDataRole.ForegroundRole:
            if column == 0:
                # Color item name based on rarity
                rarity = self.current_items[row].rarity
                return QColor(consts.COLORS[rarity])
            return QColor(consts.COLORS['white'])

        if role == Qt.ItemDataRole.BackgroundRole:
            return QColor(consts.COLORS['darkgrey'])

        return None

    def headerData(  # pylint: disable=invalid-name
        self, section: int, orientation: Qt.Orientation, role: int
    ) -> object:
        """
        Returns the data for the given role and section in the header with the specified
        orientation.
        """
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return QVariant(self.headers[section])

        return None

    def insert_items(self, items: List[m_item.Item]) -> None:
        """Inserts a list of items into the table."""
        self.beginInsertRows(QModelIndex(), 0, len(items) - 1)
        self.items.extend(items)
        self.current_items.extend(items)
        self.endInsertRows()

    def apply_filters(
        self, index: int = 1, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder
    ) -> None:
        """
        Applies a filter based on several search parameters, updating the current
        items and layout.
        """
        # Previously selected item
        selection = self.table_view.selectedIndexes()
        selected_item = self.current_items[selection[0].row()] if selection else None

        # Build list of all filters
        all_filters: List[m_filter.Filter] = m_filter.MOD_FILTERS.copy()
        for filt in m_filter.FILTERS:
            match filt:
                case m_filter.Filter():
                    all_filters.append(filt)
                case m_filter.FilterGroup(_, filters, group_box):
                    if group_box is not None and group_box.isChecked():
                        all_filters.extend(filters)

        # m_item.Items that pass every filter
        prev_time = ratelimiting.get_time_ms()
        active_filters = [
            filt
            for filt in all_filters
            if any(m_filter.filter_is_active(widget) for widget in filt.widgets)
        ]

        self.current_items = [
            item
            for item in self.items
            if all(filt.filter_func(item, *filt.widgets) for filt in active_filters)
        ]
        logger.debug(
            'Filtering took %sms: %s',
            ratelimiting.get_time_ms() - prev_time,
            active_filters,
        )

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
