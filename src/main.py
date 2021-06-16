import json

from functools import partial
from typing import Callable, Dict, List

from PyQt5.QtCore import QItemSelection
from PyQt5.QtGui import QColor, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QComboBox, QLineEdit, QWidget

from consts import COLORS
from item import Item
from gameData import CATEGORIES, FILTER_RARITIES
from mainwidget import Ui_MainWindow
from thread import DownloadThread

_jsons = ['../assets/tab1.json', '../assets/tab2.json']


def _updateTooltip(ui: Ui_MainWindow, items: List[Item], selected: QItemSelection):
    if len(selected.indexes()) == 0:
        # Occurs when filters result in nothing selected
        ui.tooltip.setText('')
        ui.tooltipImage.setText('')
    else:
        row = selected.indexes()[0].row()
        ui.tooltip.setHtml(items[row].getTooltip())
        ui.tooltipImage.setHtml(f'<img src="{items[row].filePath}" />')


def _filterRows(
    ui: Ui_MainWindow,
    items: List[Item],
    FILTERS: Dict[QWidget, Callable[[QWidget, Item], bool]],
):
    for i, item in enumerate(items):
        ui.tableView.showRow(i)
        for elem, filterFunc in FILTERS.items():
            if not filterFunc(elem, item):
                ui.tableView.hideRow(i)
                break


def _filterRarity(elem, item):
    if elem.currentText() == 'Any':
        return True
    if item.rarity.lower() == elem.currentText().lower():
        return True
    if (
        elem.currentText() == 'Any Non-Unique'
        and item.rarity != 'unique'
        and item.rarity != 'foil'
    ):
        return True

    return False


def _setupFilters(ui: Ui_MainWindow, items: List[Item]):
    # Setup filters
    FILTERS: Dict[QWidget, Callable[[QWidget, Item], bool]] = {
        ui.filterName: lambda elem, item: elem.text().lower() in item.name.lower(),
        ui.filterCategory: lambda elem, item: (
            elem.currentText() == 'Any' or item.category == elem.currentText()
        ),
        ui.filterRarity: _filterRarity,
    }

    for elem in FILTERS.keys():
        signal = None
        if type(elem) is QLineEdit:
            signal = elem.textChanged
        elif type(elem) is QComboBox:
            signal = elem.currentIndexChanged

        signal.connect(partial(_filterRows, ui, items, FILTERS))

    # Add items to combo boxes (dropdown)
    ui.filterCategory.addItems(CATEGORIES)
    ui.filterRarity.addItems(FILTER_RARITIES)


def dynamicBuild(ui: Ui_MainWindow):
    items = []
    for i, tab in enumerate(_jsons):
        # Open each tab
        with open(tab) as f:
            data = json.load(f)
            # Add each item
            for item in data['items']:
                items.append(Item(item, i))
                # Add socketed items
                if item.get('socketedItems') is not None:
                    for socketedItem in item['socketedItems']:
                        items.append(Item(socketedItem, i))
    items.sort()

    # Start downloading images
    ui.statusbar.showMessage('Downloading images')
    thread = DownloadThread(ui, items)
    thread.start()

    # Model with rows, columns
    model = QStandardItemModel(len(items), len(Item.PROPERTY_FUNCS))
    model.setHorizontalHeaderLabels(Item.PROPERTY_FUNCS.keys())
    for j, propFunc in enumerate(Item.PROPERTY_FUNCS.values()):
        for i, item in enumerate(items):
            qitem = QStandardItem(propFunc(item))
            # Only color the name
            if j == 0:
                qitem.setForeground(QColor(COLORS[item.rarity]))
            model.setItem(i, j, qitem)

    ui.tableView.setModel(model)

    _setupFilters(ui, items)

    # Connect selection to update tooltip
    ui.tableView.selectionModel().selectionChanged.connect(
        partial(_updateTooltip, ui, items)
    )

    # Hide vertical header
    ui.tableView.verticalHeader().hide()

    # Sizing
    ui.tableView.resizeRowsToContents()
    rowHeight = ui.tableView.verticalHeader().sectionSize(0)
    ui.tableView.verticalHeader().setDefaultSectionSize(rowHeight)
    ui.tableView.resizeColumnsToContents()
