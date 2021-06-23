import json

from functools import partial
from typing import Callable, Dict, List

from PyQt5 import QtCore, QtGui, QtWidgets

from consts import COLORS, SEPARATOR_TEMPLATE
from item import Item
from gameData import CATEGORIES, FILTER_RARITIES
from thread import DownloadThread

_jsons = ['../assets/tab1.json', '../assets/tab2.json']

FilterFunction = Callable[[QtWidgets.QWidget, Item], bool]


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


class Ui_MainWindow(object):
    def setupUi(self, MainWindow: QtWidgets.QMainWindow):
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

        self.tooltipImage = QtWidgets.QLabel(self.centralwidget)
        self.tooltipImage.setObjectName('tooltipImage')
        self.tooltipImage.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.tooltipImage.hide()
        self.verticalLayout.addWidget(self.tooltipImage)
        self.verticalLayout.addWidget(self.tooltip)

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
        # self.tableView.setSortingEnabled(True)
        self.tableView.setWordWrap(False)

        self.horizontalLayout.addWidget(self.tableView)
        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1280, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        self._retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self._dynamicBuild()

    def _retranslateUi(self, MainWindow: QtWidgets.QMainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate('MainWindow', 'Stash Of Exile'))
        self.groupBox.setTitle(_translate('MainWindow', 'Filters'))
        self.label.setText(_translate('MainWindow', 'Category:'))
        self.label_4.setText(_translate('MainWindow', 'Rarity:'))
        self.label_3.setText(_translate('MainWindow', 'Name:'))

    def _dynamicBuild(self):
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
        self.statusbar.showMessage('Downloading images')
        thread = DownloadThread(self.tooltipImage, self.statusbar, items)
        thread.start()

        # Model with rows, columns
        model = QtGui.QStandardItemModel(len(items), len(Item.PROPERTY_FUNCS))
        model.setHorizontalHeaderLabels(Item.PROPERTY_FUNCS.keys())
        for j, propFunc in enumerate(Item.PROPERTY_FUNCS.values()):
            for i, item in enumerate(items):
                qitem = QtGui.QStandardItem(propFunc(item))
                # Color the name by rarity
                if j == 0:
                    qitem.setForeground(QtGui.QColor(COLORS[item.rarity]))
                model.setItem(i, j, qitem)
        self.tableView.setModel(model)

        # Attach filters to widgets
        self._setupFilters(items)

        # Connect selection to update tooltip
        self.tableView.selectionModel().selectionChanged.connect(
            partial(self._updateTooltip, items)
        )

        # Hide vertical header
        self.tableView.verticalHeader().hide()

        # Sizing
        self.tableView.resizeRowsToContents()
        rowHeight = self.tableView.verticalHeader().sectionSize(0)
        self.tableView.verticalHeader().setDefaultSectionSize(rowHeight)
        self.tableView.resizeColumnsToContents()

    def _updateTooltip(self, items: List[Item], selected: QtCore.QItemSelection):
        if len(selected.indexes()) == 0:
            # Occurs when filters result in nothing selected
            self.tooltip.setText('')
            self.tooltipImage.setText('')
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
            # Set tooltip image
            self.tooltipImage.setPixmap(QtGui.QPixmap(item.filePath))

    def _filterRows(
        self, items: List[Item], FILTERS: Dict[QtWidgets.QWidget, FilterFunction]
    ):
        for i, item in enumerate(items):
            if any(not filterFunc(elem, item) for elem, filterFunc in FILTERS.items()):
                self.tableView.hideRow(i)
            else:
                self.tableView.showRow(i)

    def _setupFilters(self, items: List[Item]):
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

        # Connect filter function with the widget
        for elem in FILTERS.keys():
            signal = None
            if type(elem) is QtWidgets.QLineEdit:
                signal = elem.textChanged
            elif type(elem) is QtWidgets.QComboBox:
                signal = elem.currentIndexChanged

            signal.connect(partial(self._filterRows, items, FILTERS))

        # Add items to combo boxes (dropdown)
        self.filterCategory.addItems(CATEGORIES)
        self.filterRarity.addItems(FILTER_RARITIES)
