"""
Handles viewing items in tabs and characters.
"""

import json
import os

from dataclasses import field
from functools import partial
from inspect import signature
from typing import List, TYPE_CHECKING, Optional, Set, Tuple

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
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import log
import util

from consts import SEPARATOR_TEMPLATE
from item.filter import FILTERS
from item.item import Item
from gamedata import COMBO_ITEMS
from save import Account
from tab import CharacterTab, ItemTab, StashTab
from table import TableModel
from thread.thread import Call

if TYPE_CHECKING:
    from mainwindow import MainWindow

logger = log.get_logger(__name__)

ITEM_CACHE_DIR = os.path.join('..', 'item_cache')
TABS_DIR = 'tabs'
CHARACTER_DIR = 'characters'


class MainWidget(QWidget):
    """Main Widget for the filter, tooltip, and table view."""

    def __init__(self, main_window: 'MainWindow') -> None:
        """Initialize the UI."""
        QWidget.__init__(self)
        self.main_window = main_window
        self.item_tabs: List[ItemTab] = []
        self.account = None
        self._static_build()
        self._dynamic_build_filters()
        self._setup_filters()
        self._name_ui()

    def on_show(
        self,
        account: Optional[Account] = None,
        league: str = '',
        tabs: List[int] = field(default_factory=list),
        characters: List[str] = field(default_factory=list),
    ) -> None:
        """Retrieves existing tabs or send API calls, then build the table."""
        if account is None:
            # Show all cached results
            for accounts in util.get_subdirectories(ITEM_CACHE_DIR):
                for leagues in util.get_subdirectories(accounts):
                    tab_dir = os.path.join(leagues, TABS_DIR)
                    character_dir = os.path.join(leagues, CHARACTER_DIR)
                    self.item_tabs.extend(
                        StashTab(tab) for tab in util.get_jsons(tab_dir)
                    )
                    self.item_tabs.extend(
                        CharacterTab(char) for char in util.get_jsons(character_dir)
                    )
        else:
            self._send_api(account, league, tabs, characters)

        self._build_table()

    def _send_api(
        self, account: Account, league: str, tabs: List[int], characters: List[str]
    ) -> None:
        """
        Generates and sends API calls based on selected league, tabs, and characters.
        """
        # TODO: force import vs cache
        self.account = account
        api_manager = self.main_window.api_manager

        logger.debug('Begin checking cache')

        api_calls: List[Call] = []
        for tab_num in tabs:
            filename = os.path.join(
                ITEM_CACHE_DIR, account.username, league, TABS_DIR, f'{tab_num}.json'
            )
            tab = StashTab(filename, tab_num)
            if os.path.exists(filename):
                self.item_tabs.append(tab)
                continue
            api_call = Call(
                api_manager.get_tab_items,
                (account.username, account.poesessid, league, tab_num),
                self,
                self._get_stash_tab_callback,
                (tab,),
            )
            api_calls.append(api_call)

        for char in characters:
            filename = os.path.join(
                ITEM_CACHE_DIR, account.username, league, CHARACTER_DIR, f'{char}.json'
            )
            tab = CharacterTab(filename, char)
            if os.path.exists(filename):
                self.item_tabs.append(tab)
                continue
            api_call = Call(
                api_manager.get_character_items,
                (account.username, account.poesessid, char),
                self,
                self._get_char_callback,
                (tab,),
            )
            api_calls.append(api_call)

        api_manager.insert(api_calls)

    def _on_receive_items(self, items: List[Item]):
        """Inserts items in model and queues image downloading."""
        icons: Set[Tuple[str, str]] = set()
        download_manager = self.main_window.download_manager
        icons.update((item.icon, item.file_path) for item in items)
        download_manager.insert(
            Call(download_manager.get_image, icon, None) for icon in icons
        )
        self.model.insert_items(items)

    def _get_stash_tab_callback(self, tab: StashTab, data, err_message: str) -> None:
        """Takes tab API data and inserts the items into the table."""
        if data is None:
            # Use error message
            logger.warning(err_message)
            return

        assert self.account is not None

        logger.info('Writing tab json to %s', tab.filepath)
        util.create_directories(tab.filepath)
        with open(tab.filepath, 'w') as f:
            json.dump(data, f)

        self._on_receive_items(tab.get_items())

    def _get_char_callback(self, tab: CharacterTab, data, err_message: str) -> None:
        """Takes character API data and inserts the items into the table."""
        if data is None:
            # Use error message
            logger.warning(err_message)
            return

        logger.info('Writing character json to %s', tab.filepath)
        util.create_directories(tab.filepath)
        with open(tab.filepath, 'w') as f:
            json.dump(data, f)

        self._on_receive_items(tab.get_items())

    def _build_table(self) -> None:
        """Sets up the items, downloads their images, and sets up the table."""
        # Get available items
        # TODO: delegate this to APIManager or new thread to avoid blocking UI
        download_manager = self.main_window.download_manager
        items: List[Item] = []
        icons: Set[Tuple[str, str]] = set()
        for tab in self.item_tabs:
            # Open each tab
            # logger.debug(tab.filepath)
            tab_items = tab.get_items()
            icons.update((item.icon, item.file_path) for item in tab_items)
            items.extend(tab_items)

        download_manager.insert(
            Call(download_manager.get_image, icon, None) for icon in icons
        )
        logger.debug('Cached tabs: %s, items: %s', len(self.item_tabs), len(items))
        self.item_tabs = []

        # Insert first item and use its height as default
        self.model.insert_items(items[0:1])
        self.table.resizeRowToContents(0)
        row_height = self.table.verticalHeader().sectionSize(0)
        self.table.verticalHeader().setDefaultSectionSize(row_height)

        # Insert remaining items
        self.model.insert_items(items[1:])

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

        # Remaining resizing
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.resizeColumnToContents(0)

    def _static_build(self) -> None:
        """Sets up the static base UI, including properties and widgets."""
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
        """Sets up the filter widgets and labels."""
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
        self.model.set_filter_widgets(self.widgets)

    def _name_ui(self) -> None:
        """Names the UI elements, including window title and labels."""
        self.filter_group_box.setTitle('Filters')

        # Name filters
        for filt, label in zip(FILTERS, self.labels):
            label.setText(f'{filt.name}:')

    def _update_tooltip(self, model: TableModel, selected: QItemSelection) -> None:
        """Updates item tooltip, triggered when a row is clicked."""
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
        """Initializes filters and links to widgets."""
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
