import json

from functools import partial
from typing import List
from PyQt6.QtCore import QItemSelection, QRect, QSize, Qt
from PyQt6.QtGui import QFont, QFontDatabase, QTextCursor

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QStatusBar,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from consts import SEPARATOR_TEMPLATE
from filter import FILTERS
from item import Item
from gameData import COMBO_ITEMS
from table import TableModel
from thread import DownloadThread

_jsons = ['../assets/tab1.json', '../assets/tab2.json']


class Ui_MainWindow(object):
    """Custom Main Window."""

    def __init__(self, MainWindow: QMainWindow) -> None:
        self._staticBuild(MainWindow)
        self._dynamicBuildFilters()
        self._dynamicBuildTable()
        self._nameUi(MainWindow)

    def _staticBuild(self, MainWindow: QMainWindow) -> None:
        """Setup the static base UI, including properties and widgets."""
        MainWindow.resize(1280, 720)

        # A font by Jos Buivenga (exljbris) -> www.exljbris.com
        QFontDatabase.addApplicationFont('../assets/FontinSmallCaps.ttf')
        with open('styles.qss', 'r') as f:
            MainWindow.setStyleSheet(f.read())

        # Main Area
        self.centralWidget = QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralWidget)
        self.mainHorizontalLayout = QHBoxLayout(self.centralWidget)

        # Filter Area
        self.filter = QVBoxLayout()
        self.filterGroupBox = QGroupBox()
        self.filter.addWidget(self.filterGroupBox)
        self.filterFormLayout = QFormLayout()
        self.filterVerticalLayout = QVBoxLayout(self.filterGroupBox)
        self.filterVerticalLayout.addLayout(self.filterFormLayout)

        # Tooltip
        self.tooltip = QTextEdit()
        self.tooltip.setReadOnly(True)
        self.tooltip.setFont(QFont('Fontin SmallCaps', 12))
        self.tooltip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tooltip.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tooltip.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # Item Table
        self.tableView = QTableView()
        self.tableView.setMinimumSize(QSize(200, 0))
        self.tableView.setMouseTracking(True)
        self.tableView.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents
        )
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableView.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tableView.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tableView.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        self.tableView.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        self.tableView.setShowGrid(False)
        self.tableView.setWordWrap(False)
        self.tableView.setSortingEnabled(True)

        # Custom Table Model
        self.model = TableModel(MainWindow)
        self.tableView.setModel(self.model)

        # Add to main layout and set stretch ratios
        self.mainHorizontalLayout.addLayout(self.filter)
        self.mainHorizontalLayout.addWidget(self.tooltip)
        self.mainHorizontalLayout.addWidget(self.tableView)
        self.mainHorizontalLayout.setStretch(0, 1)
        self.mainHorizontalLayout.setStretch(1, 2)
        self.mainHorizontalLayout.setStretch(2, 3)

        # Menu bar
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setGeometry(QRect(0, 0, 1280, 21))
        MainWindow.setMenuBar(self.menubar)

        # Status bar
        self.statusbar = QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

    def _dynamicBuildFilters(self) -> None:
        """Setup the filter widgets and labels."""
        self.labels: List[QLabel] = []
        self.widgets: List[QWidget] = []
        for i, filter in enumerate(FILTERS):
            label = QLabel(self.filterGroupBox)
            self.labels.append(label)
            widget = filter.widget()
            self.widgets.append(widget)
            self.filterFormLayout.setWidget(i, QFormLayout.ItemRole.LabelRole, label)
            self.filterFormLayout.setWidget(i, QFormLayout.ItemRole.FieldRole, widget)

    def _dynamicBuildTable(self) -> None:
        """Setup the items, download their images, and setup the table."""

        items: List[Item] = []
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
        self.model.insertItems(items)

        # Start downloading images
        self.statusbar.showMessage('Downloading images')
        thread = DownloadThread(self.statusbar, items)
        thread.start()

        # Attach filters to widgets
        self._setupFilters(items)

        # Connect selection to update tooltip
        # pyright: reportFunctionMemberAccess=false
        self.tableView.selectionModel().selectionChanged.connect(
            partial(self._updateTooltip, items)
        )

        # Sizing
        self.tableView.resizeRowsToContents()
        rowHeight = self.tableView.verticalHeader().sectionSize(0)
        self.tableView.verticalHeader().setDefaultSectionSize(rowHeight)
        self.tableView.resizeColumnsToContents()

    def _nameUi(self, MainWindow: QMainWindow) -> None:
        """Name the UI elements, including window title and labels."""
        MainWindow.setWindowTitle('Stash Of Exile')
        self.filterGroupBox.setTitle('Filters')
        for filter, label in zip(FILTERS, self.labels):
            label.setText(f'{filter.name}:')

    def _updateTooltip(self, items: List[Item], selected: QItemSelection) -> None:
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
                self.tooltip.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if i != len(sections) - 1:
                    self.tooltip.append(
                        SEPARATOR_TEMPLATE.format('../assets/SeparatorWhite.png', width)
                    )

            # Reset scroll to top
            self.tooltip.moveCursor(QTextCursor.MoveOperation.Start)

    def _filterRows(self, items: List[Item]) -> None:
        """Iterate through item list, showing or hiding each depending on the filters."""
        for i, (item, widget) in enumerate(zip(items, self.widgets)):
            if any(not filter.filterFunc(widget, item) for filter in FILTERS):
                self.tableView.hideRow(i)
            else:
                self.tableView.showRow(i)

    def _setupFilters(self, items: List[Item]) -> None:
        """Initialize filters and link to widgets."""
        # Key: widget that filter applies to
        # Value: FilterFunction (takes in element and item, returns whether to show the item)

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
        for filter, widget in zip(FILTERS, self.widgets):
            options = COMBO_ITEMS.get(filter.name)
            if options is not None:
                assert isinstance(widget, QComboBox)
                widget.addItems(options)
