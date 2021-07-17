import json

from functools import partial
from inspect import signature
from typing import List, TYPE_CHECKING
from PyQt6.QtCore import QItemSelection, QSize, Qt
from PyQt6.QtGui import QFont, QIntValidator, QTextCursor

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QStatusBar,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from consts import SEPARATOR_TEMPLATE
from filter import FILTERS
from item import Item
from gamedata import COMBO_ITEMS
from table import TableModel
from thread import DownloadThread

if TYPE_CHECKING:
    from mainwindow import MainWindow


_jsons = ['../assets/tab1.json', '../assets/tab2.json']


class MainWidget(QWidget):
    """Main Widget for the filter, tooltip, and table view."""

    def __init__(self, mainWindow: 'MainWindow') -> None:
        """Initialize the UI."""
        QWidget.__init__(self)
        self.mainWindow = mainWindow
        self._staticBuild()
        self._dynamicBuildFilters()
        self._setupFilters()
        self._nameUi()

    def onShow(self):
        pass

    def buildTable(self) -> None:
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
        statusBar: QStatusBar = self.parent().statusBar()
        statusBar.showMessage('Downloading images')
        thread = DownloadThread(statusBar, items)
        thread.start()

        # Connect selection to update tooltip
        self.table.selectionModel().selectionChanged.connect(
            partial(self._updateTooltip, self.model)
        )

        # Sizing
        self.table.resizeRowsToContents()
        rowHeight = self.table.verticalHeader().sectionSize(0)
        self.table.verticalHeader().setDefaultSectionSize(rowHeight)
        self.table.resizeColumnsToContents()

    def _staticBuild(self) -> None:
        """Setup the static base UI, including properties and widgets."""
        # Main Area
        self.mainHorizontalLayout = QHBoxLayout(self)

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
        self.table = QTableView()
        self.table.setMinimumSize(QSize(200, 0))
        self.table.setMouseTracking(True)
        self.table.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents
        )
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.setSortingEnabled(True)

        # Custom Table Model
        self.model = TableModel(self.table, parent=self)
        self.table.setModel(self.model)

        # Add to main layout and set stretch ratios
        self.mainHorizontalLayout.addLayout(self.filter)
        self.mainHorizontalLayout.addWidget(self.tooltip)
        self.mainHorizontalLayout.addWidget(self.table)
        self.mainHorizontalLayout.setStretch(0, 1)
        self.mainHorizontalLayout.setStretch(1, 2)
        self.mainHorizontalLayout.setStretch(2, 3)

        # Int validator
        self.intValidator = QIntValidator()

    def _dynamicBuildFilters(self) -> None:
        """Setup the filter widgets and labels."""
        self.labels: List[QLabel] = []
        self.widgets: List[List[QWidget]] = []
        for i, filter in enumerate(FILTERS):
            # Label
            label = QLabel(self.filterGroupBox)
            self.labels.append(label)
            self.filterFormLayout.setWidget(i, QFormLayout.ItemRole.LabelRole, label)

            # Widget layout
            layout = QHBoxLayout()
            widgets: List[QWidget] = []
            # Create widgets based on the number of arguments filterFunc takes in
            for _ in range(len(signature(filter.filterFunc).parameters) - 1):
                # Create widget object
                widget = filter.widget()
                widgets.append(widget)
                layout.addWidget(widget)
                if filter.widget == QLineEdit and filter.numericOnly:
                    assert isinstance(widget, QLineEdit)
                    widget.setValidator(self.intValidator)

            layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            self.widgets.append(widgets)
            self.filterFormLayout.setLayout(i, QFormLayout.ItemRole.FieldRole, layout)

        # Send widgets to model
        self.model.setWidgets(self.widgets)

    def _nameUi(self) -> None:
        """Name the UI elements, including window title and labels."""
        self.filterGroupBox.setTitle('Filters')

        # Name filters
        for filter, label in zip(FILTERS, self.labels):
            label.setText(f'{filter.name}:')

    def _updateTooltip(self, model: TableModel, selected: QItemSelection) -> None:
        """Update item tooltip, triggered when a row is clicked."""
        if len(selected.indexes()) == 0:
            # Nothing selected
            return

        row = selected.indexes()[0].row()
        item = model.currentItems[row]

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

    def _setupFilters(self) -> None:
        """Initialize filters and link to widgets."""
        for filter, widgets in zip(FILTERS, self.widgets):
            signal = None
            for widget in widgets:
                # Get signal based on widget type
                if isinstance(widget, QLineEdit):
                    signal = widget.textChanged
                elif isinstance(widget, QComboBox):
                    signal = widget.currentIndexChanged
                elif isinstance(widget, QCheckBox):
                    signal = widget.stateChanged

                if signal is not None:
                    signal.connect(self.model.applyFilters)

        # Add items to combo boxes (dropdown)
        for filter, widgets in zip(FILTERS, self.widgets):
            options = COMBO_ITEMS.get(filter.name)
            if options is not None:
                widget = widgets[0]
                assert isinstance(widget, QComboBox)
                widget.addItems(options)
