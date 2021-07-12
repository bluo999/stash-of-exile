import json

from functools import partial
from typing import Callable, Dict, List

from PyQt5 import QtCore, QtGui, QtWidgets

from consts import COLORS, SEPARATOR_TEMPLATE
from item import Item
from gameData import CATEGORIES, FILTER_RARITIES
from table import TableModel
from thread import DownloadThread

_jsons = ['../assets/tab1.json', '../assets/tab2.json']

FilterFunction = Callable[[QtWidgets.QWidget, Item], bool]


def _filterRarity(elem, item):
    """Filter function that determines rarity."""
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


class Ui_MainWindow(object):
    """Custom Main Window."""

    def staticBuild(self, MainWindow: QtWidgets.QMainWindow) -> None:
        """Setup the static base UI, including properties and widgets."""
        MainWindow.setObjectName('MainWindow')
        MainWindow.resize(1280, 720)

        # A font by Jos Buivenga (exljbris) -> www.exljbris.com
        QtGui.QFontDatabase.addApplicationFont('../assets/FontinSmallCaps.ttf')
        with open('styles.qss', 'r') as f:
            MainWindow.setStyleSheet(f.read())

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox)
        self.formLayout = QtWidgets.QFormLayout()
        self.label = QtWidgets.QLabel(self.groupBox)
        self.formLayout.setWidget(
            2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label
        )
        self.filterCategory = QtWidgets.QComboBox(self.groupBox)
        self.formLayout.setWidget(
            2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.filterCategory
        )

        self.filterRarity = QtWidgets.QComboBox(self.groupBox)
        self.formLayout.setWidget(
            3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.filterRarity
        )
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.formLayout.setWidget(
            3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_4
        )
        self.filterName = QtWidgets.QLineEdit(self.groupBox)
        self.formLayout.setWidget(
            0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.filterName
        )
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.formLayout.setWidget(
            0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_3
        )
        self.verticalLayout_2.addLayout(self.formLayout)
        self.verticalLayout.addWidget(self.groupBox)

        self.tooltip = QtWidgets.QTextEdit(self.centralwidget)
        self.tooltip.setReadOnly(True)
        self.tooltip.setFont(QtGui.QFont('Fontin SmallCaps', 12))
        self.tooltip.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.tooltip.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.tooltip.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )

        self.horizontalLayout.addLayout(self.verticalLayout)

        self.tableView = QtWidgets.QTableView(self.centralwidget)
        self.tableView.setMinimumSize(QtCore.QSize(200, 0))
        self.tableView.setMouseTracking(True)
        self.tableView.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.AdjustToContents
        )
        self.tableView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableView.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.tableView.setHorizontalScrollMode(
            QtWidgets.QAbstractItemView.ScrollPerPixel
        )
        self.tableView.setShowGrid(False)
        self.tableView.setWordWrap(False)
        self.tableView.setSortingEnabled(True)

        # Custom Model
        self.model = TableModel()
        self.tableView.setModel(self.model)

        self.horizontalLayout.addWidget(self.tooltip)
        self.horizontalLayout.addWidget(self.tableView)
        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 2)
        self.horizontalLayout.setStretch(2, 3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1280, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        self._nameUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self._dynamicBuild()

    def _nameUi(self, MainWindow: QtWidgets.QMainWindow) -> None:
        """Name the UI elements, including window title and labels."""
        MainWindow.setWindowTitle('Stash Of Exile')
        self.groupBox.setTitle('Filters')
        self.label.setText('Category:')
        self.label_4.setText('Rarity:')
        self.label_3.setText('Name:')

    def _dynamicBuild(self) -> None:
        """Setup the items, download their images, and setup the table."""
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
        self.model.insertRows(0, items)

        # Start downloading images
        self.statusbar.showMessage('Downloading images')
        thread = DownloadThread(self.statusbar, items)
        thread.start()

        # Attach filters to widgets
        self._setupFilters(items)

        # Connect selection to update tooltip
        self.tableView.selectionModel().selectionChanged.connect(
            partial(self._updateTooltip, items)
        )

        # Sizing
        self.tableView.resizeRowsToContents()
        rowHeight = self.tableView.verticalHeader().sectionSize(0)
        self.tableView.verticalHeader().setDefaultSectionSize(rowHeight)
        self.tableView.resizeColumnsToContents()

    def _updateTooltip(
        self, items: List[Item], selected: QtCore.QItemSelection
    ) -> None:
        """Update item tooltip, triggered when a row is clicked."""
        if len(selected.indexes()) == 0:
            # Occurs when filters result in nothing selected
            self.tooltip.setText('')
        else:
            row = selected.indexes()[0].row()
            item = items[row]

            self.tooltip.setHtml('')
            sections = item.getTooltip()
            width = self.tooltip.width() - self.tooltip.verticalScrollBar().width()

            # Construct tooltip from sections
            for i, html in enumerate(sections):
                self.tooltip.append(html)
                self.tooltip.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                if i != len(sections) - 1:
                    self.tooltip.append(
                        SEPARATOR_TEMPLATE.format('../assets/SeparatorWhite.png', width)
                    )

            # Reset scroll to top
            self.tooltip.moveCursor(QtGui.QTextCursor.MoveOperation.Start)

    def _filterRows(
        self, items: List[Item], FILTERS: Dict[QtWidgets.QWidget, FilterFunction]
    ) -> None:
        """Iterate through item list, showing or hiding each depending on the filters."""
        for i, item in enumerate(items):
            if any(not filterFunc(elem, item) for elem, filterFunc in FILTERS.items()):
                self.tableView.hideRow(i)
            else:
                self.tableView.showRow(i)

    def _setupFilters(self, items: List[Item]) -> None:
        """Initialize filters and link to widgets."""
        # Key: widget that filter applies to
        # Value: FilterFunction (takes in element and item, returns whether to show the item)
        FILTERS: Dict[QtWidgets.QWidget, FilterFunction] = {
            self.filterName: lambda elem, item: (
                elem.text().lower() in item.name.lower()
            ),
            self.filterCategory: lambda elem, item: (
                elem.currentText() == 'Any' or item.category == elem.currentText()
            ),
            self.filterRarity: _filterRarity,
        }

        # # Connect filter function with the widget
        # for elem in FILTERS.keys():
        #     signal = None
        #     if type(elem) is QtWidgets.QLineEdit:
        #         signal = elem.textChanged
        #     elif type(elem) is QtWidgets.QComboBox:
        #         signal = elem.currentIndexChanged

        #     if signal is not None:
        #         signal.connect(partial(self._filterRows, items, FILTERS))

        # Add items to combo boxes (dropdown)
        self.filterCategory.addItems(CATEGORIES)
        self.filterRarity.addItems(FILTER_RARITIES)
