"""
Handles viewing items in tabs and characters.
"""

import json
import os

from dataclasses import field
from functools import partial
from inspect import signature
from typing import List, TYPE_CHECKING, Tuple

from PyQt6.QtCore import QItemSelection, QSize, Qt
from PyQt6.QtGui import QFont, QTextCursor
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

import log

from consts import SEPARATOR_TEMPLATE
from filter import FILTERS
from item import Item
from gamedata import COMBO_ITEMS
from save import Account
from table import TableModel
from thread import DownloadThread
from util import create_directories, get_jsons, get_subdirectories

if TYPE_CHECKING:
    from mainwindow import MainWindow

logger = log.get_logger(__name__)

ITEM_CACHE_DIR = os.path.join('..', 'item_cache')


class MainWidget(QWidget):
    """Main Widget for the filter, tooltip, and table view."""

    def __init__(self, main_window: 'MainWindow') -> None:
        """Initialize the UI."""
        QWidget.__init__(self)
        self.main_window = main_window
        self.paths: List[Tuple[str, str]] = []
        self.num_tabs = 0
        self._static_build()
        self._dynamic_build_filters()
        self._setup_filters()
        self._name_ui()

    def on_show(
        self,
        account: Account = None,
        league: str = '',
        characters: List[str] = field(default_factory=list),
        tabs: List[int] = field(default_factory=list),
    ):
        """Use cached items and retrieve the remainder using the API."""
        # TODO: use tabs
        # self.paths represents the paths that still need to be imported into the table
        if account is None:
            # Show all cached results
            self.paths = [
                (os.path.splitext(os.path.basename(path))[0], path)
                for accounts in get_subdirectories(ITEM_CACHE_DIR)
                for leagues in get_subdirectories(accounts)
                for path in get_jsons(leagues)
            ]
        else:
            # Download jsons
            for char in characters:
                filename = os.path.join(
                    ITEM_CACHE_DIR, account.username, league, f'{char}.json'
                )
                # TODO: force import vs cache
                if os.path.exists(filename):
                    self.paths.append((char, filename))
                    continue
                create_directories(filename)
                api_manager = self.main_window.api_manager
                api_manager.insert(
                    api_manager.get_character_items,
                    (account.username, account.poesessid, char),
                    self,
                    self._get_char_callback,
                    (char, filename),
                )

        self._build_table()

    def _get_char_callback(
        self, char_name: str, filename: str, char, err_message: str
    ) -> None:
        """Takes character API data and inserts the items into the table."""
        if char is None:
            # Use error message
            logger.warning(err_message)
            return

        logger.info('Writing character json to %s', filename)
        with open(filename, 'w') as f:
            json.dump(char, f)

        items = self._parse_tab(filename, char_name)
        self.model.insert_items(items)

    def _parse_tab(self, tab: str, tab_name: str = '') -> List[Item]:
        """Parses a tab or character, extracting all items and socketed items."""
        items: List[Item] = []
        if tab_name == '':
            tab_name = str(self.num_tabs)
        with open(tab, 'r') as f:
            data = json.load(f)
            # Add each item
            for item in data['items']:
                items.append(Item(item, tab_name))
                # Add socketed items
                if item.get('socketedItems') is not None:
                    for socketed_item in item['socketedItems']:
                        items.append(Item(socketed_item, tab_name))
        self.num_tabs += 1
        items.sort()
        return items

    def _build_table(self) -> None:
        """Setup the items, download their images, and setup the table."""
        # Get available items
        logger.debug(self.paths)
        items: List[Item] = []
        for (tab_name, tab) in self.paths:
            # Open each tab
            items.extend(self._parse_tab(tab, tab_name))
        self.paths = []
        self.model.insert_items(items)

        # # Start downloading images
        # status_bar: QStatusBar = self.main_window.statusBar()
        # status_bar.showMessage('Downloading images')
        # thread = DownloadThread(status_bar, items)
        # thread.start()
        # Connect selection to update tooltip

        self.table.selectionModel().selectionChanged.connect(
            partial(self._update_tooltip, self.model)
        )

        # Connect sort
        self.table.horizontalHeader().sortIndicatorChanged.connect(
            lambda logicalIndex, order: self.model.apply_filters(
                index=logicalIndex, order=order
            )
        )

        # Sizing
        self.table.resizeRowsToContents()
        row_height = self.table.verticalHeader().sectionSize(0)
        self.table.verticalHeader().setDefaultSectionSize(row_height)
        self.table.resizeColumnsToContents()

    def _static_build(self) -> None:
        """Setup the static base UI, including properties and widgets."""
        # Main Area
        self.main_hlayout = QHBoxLayout(self)

        # Filter Area
        self.filter = QVBoxLayout()
        self.filter_group_box = QGroupBox()
        self.filter.addWidget(self.filter_group_box)
        self.filter_form_layout = QFormLayout()
        self.filter_vlayout = QVBoxLayout(self.filter_group_box)
        self.filter_vlayout.addLayout(self.filter_form_layout)

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
        self.table.horizontalHeader().setSectionsMovable(True)

        # Custom Table Model
        self.model = TableModel(self.table, parent=self)
        self.table.setModel(self.model)

        # Add to main layout and set stretch ratios
        self.main_hlayout.addLayout(self.filter)
        self.main_hlayout.addWidget(self.tooltip)
        self.main_hlayout.addWidget(self.table)
        self.main_hlayout.setStretch(0, 1)
        self.main_hlayout.setStretch(1, 2)
        self.main_hlayout.setStretch(2, 3)

    def _dynamic_build_filters(self) -> None:
        """Setup the filter widgets and labels."""
        self.labels: List[QLabel] = []
        self.widgets: List[List[QWidget]] = []
        for i, filt in enumerate(FILTERS):
            # Label
            label = QLabel(self.filter_group_box)
            self.labels.append(label)
            self.filter_form_layout.setWidget(i, QFormLayout.ItemRole.LabelRole, label)

            # Widget layout
            layout = QHBoxLayout()
            widgets: List[QWidget] = []
            # Create widgets based on the number of arguments filterFunc takes in
            for _ in range(len(signature(filt.filter_func).parameters) - 1):
                # Create widget object
                widget = filt.widget()
                widgets.append(widget)
                layout.addWidget(widget)
                if filt.widget == QLineEdit and filt.validator is not None:
                    assert isinstance(widget, QLineEdit)
                    widget.setValidator(filt.validator)

            layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            self.widgets.append(widgets)
            self.filter_form_layout.setLayout(i, QFormLayout.ItemRole.FieldRole, layout)

        # Send widgets to model
        self.model.set_widgets(self.widgets)

    def _name_ui(self) -> None:
        """Name the UI elements, including window title and labels."""
        self.filter_group_box.setTitle('Filters')

        # Name filters
        for filt, label in zip(FILTERS, self.labels):
            label.setText(f'{filt.name}:')

    def _update_tooltip(self, model: TableModel, selected: QItemSelection) -> None:
        """Update item tooltip, triggered when a row is clicked."""
        if len(selected.indexes()) == 0:
            # Nothing selected
            return

        row = selected.indexes()[0].row()
        item = model.current_items[row]

        self.tooltip.setHtml('')
        sections = item.get_tooltip()
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

    def _setup_filters(self) -> None:
        """Initialize filters and link to widgets."""
        for filt, widgets in zip(FILTERS, self.widgets):
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
                    signal.connect(
                        partial(
                            self.model.apply_filters,
                            index=1,
                            order=Qt.SortOrder.AscendingOrder,
                        )
                    )

        # Add items to combo boxes (dropdown)
        for filt, widgets in zip(FILTERS, self.widgets):
            options = COMBO_ITEMS.get(filt.name)
            if options is not None:
                widget = widgets[0]
                assert isinstance(widget, QComboBox)
                widget.addItems(options)
