"""
Handles viewing items in tabs and characters.
"""

import dataclasses
import inspect
import json
import os
import pickle

from typing import List, TYPE_CHECKING, Optional, Set, Tuple

from PyQt6.QtCore import QItemSelection, QSize, Qt
from PyQt6.QtGui import QDoubleValidator, QFont, QTextCursor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from stashofexile import consts, gamedata, log, save, tab as m_tab, table, util
from stashofexile.items import filter as m_filter, item as m_item, moddb
from stashofexile.threads import thread
from stashofexile.widgets import editcombo

if TYPE_CHECKING:
    import mainwindow

logger = log.get_logger(__name__)

MOD_DB_FILE = os.path.join('item_db.pkl')
ITEM_CACHE_DIR = os.path.join('item_cache')

TABS_DIR = 'tabs'
CHARACTER_DIR = 'characters'
JEWELS_DIR = 'jewels'


def _toggle_visibility(widget: QWidget) -> None:
    """Toggles the visibility of a widget."""
    widget.setVisible(not widget.isVisible())


def _populate_combo(filt: m_filter.Filter) -> None:
    """Populates a filter's combo box if necessary."""
    if (options := gamedata.COMBO_ITEMS.get(filt.name)) is not None:
        widget = filt.widgets[0]
        assert isinstance(widget, QComboBox)
        widget.addItems(options)


class MainWidget(QWidget):
    """Main Widget for the filter, tooltip, and table view."""

    def __init__(self, main_window: 'mainwindow.MainWindow') -> None:
        """Initialize the UI."""
        super().__init__()
        self.main_window = main_window
        self.item_tabs: List[m_tab.ItemTab] = []
        self.account = None
        self.mod_db: moddb.ModDb = moddb.ModDb()
        self.tab_filt: Optional[m_filter.Filter] = None
        self._static_build()
        self._load_mod_file()
        self._dynamic_build_filters()
        self._setup_filters()
        self._name_ui()

    def on_show(
        self,
        account: save.Account,
        league: str,
        tabs: List[int] = dataclasses.field(default_factory=list),
        characters: List[str] = dataclasses.field(default_factory=list),
    ) -> None:
        """Retrieves existing tabs or send API calls, then build the table."""
        if account.poesessid == '':
            # Show all cached results
            league_dir = os.path.join(ITEM_CACHE_DIR, account.username, league)

            tab_dir = os.path.join(league_dir, TABS_DIR)
            character_dir = os.path.join(league_dir, CHARACTER_DIR)
            jewels_dir = os.path.join(league_dir, JEWELS_DIR)

            if (stash := util.get_jsons(tab_dir)) is not None:
                self.item_tabs.extend(m_tab.StashTab(stash_tab) for stash_tab in stash)
            if (chars := util.get_jsons(character_dir)) is not None:
                self.item_tabs.extend(m_tab.CharacterTab(char) for char in chars)
            if (jewels := util.get_jsons(jewels_dir)) is not None:
                self.item_tabs.extend(m_tab.CharacterTab(char) for char in jewels)
        else:
            self._send_api(account, league, tabs, characters)

        self._build_table()

    def _send_api(
        self, account: save.Account, league: str, tabs: List[int], characters: List[str]
    ) -> None:
        """
        Generates and sends API calls based on selected league, tabs, and characters.
        """
        # TODO: force import vs cache
        self.account = account
        api_manager = self.main_window.api_manager

        logger.debug('Begin checking cache')

        api_calls: List[thread.Call] = []
        # Queue stash tab API calls
        for tab_num in tabs:
            filename = os.path.join(
                ITEM_CACHE_DIR, account.username, league, TABS_DIR, f'{tab_num}.json'
            )
            item_tab = m_tab.StashTab(filename, tab_num)
            if os.path.exists(filename):
                self.item_tabs.append(item_tab)
                continue
            api_call = thread.Call(
                api_manager.get_tab_items,
                (account.username, account.poesessid, league, tab_num),
                self,
                self._get_stash_tab_callback,
                (item_tab,),
            )
            api_calls.append(api_call)

        # Queue character items API calls
        for char in characters:
            filename = os.path.join(
                ITEM_CACHE_DIR, account.username, league, CHARACTER_DIR, f'{char}.json'
            )
            item_tab = m_tab.CharacterTab(filename, char)
            if os.path.exists(filename):
                self.item_tabs.append(item_tab)
                continue
            api_call = thread.Call(
                api_manager.get_character_items,
                (account.username, account.poesessid, char),
                self,
                self._get_char_callback,
                (item_tab,),
            )
            api_calls.append(api_call)

        # Queue jewels API calls
        for char in characters:
            filename = os.path.join(
                ITEM_CACHE_DIR, account.username, league, JEWELS_DIR, f'{char}.json'
            )
            item_tab = m_tab.CharacterTab(filename, char)
            if os.path.exists(filename):
                self.item_tabs.append(item_tab)
                continue
            api_call = thread.Call(
                api_manager.get_character_jewels,
                (account.username, account.poesessid, char),
                self,
                self._get_char_callback,
                (item_tab,),
            )
            api_calls.append(api_call)

        api_manager.insert(api_calls)

    def _on_receive_items(self, items: List[m_item.Item]) -> None:
        """Inserts items in model and queues image downloading."""
        icons: Set[Tuple[str, str]] = set()
        download_manager = self.main_window.download_manager
        icons.update((item.icon, item.file_path) for item in items)
        download_manager.insert(
            thread.Call(download_manager.get_image, icon, None) for icon in icons
        )
        self.model.insert_items(items)
        self.mod_db.insert_items(items)
        if self.tab_filt is not None:
            widget = self.tab_filt.widgets[0]
            assert isinstance(widget, QComboBox)
            widget.addItem(items[0].tab)

    def _get_stash_tab_callback(
        self, tab: m_tab.StashTab, data, err_message: str
    ) -> None:
        """Takes tab API data and inserts the items into the table."""
        if data is None:
            # Use error message
            logger.warning(err_message)
            return

        assert self.account is not None

        logger.info('Writing tab json to %s', tab.filepath)
        util.create_directories(tab.filepath)
        with open(tab.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        self.main_window.statusBar().showMessage(
            f'Stash tab received: {tab.tab_num}', consts.STATUS_TIMEOUT
        )
        self._on_receive_items(tab.get_items())

    def _get_char_callback(
        self, tab: m_tab.CharacterTab, data, err_message: str
    ) -> None:
        """Takes character API data and inserts the items into the table."""
        if data is None:
            # Use error message
            logger.warning(err_message)
            return

        logger.info('Writing character json to %s', tab.filepath)
        util.create_directories(tab.filepath)
        with open(tab.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        self.main_window.statusBar().showMessage(
            f'Character items received: {tab.char_name}', consts.STATUS_TIMEOUT
        )
        self._on_receive_items(tab.get_items())

    def _build_table(self) -> None:
        """Sets up the items, downloads their images, and sets up the table."""
        # Get available items
        download_manager = self.main_window.download_manager
        items: List[m_item.Item] = []
        icons: Set[Tuple[str, str]] = set()
        for tab in self.item_tabs:
            # Open each tab
            # logger.debug(tab.filepath)
            tab_items = tab.get_items()
            icons.update((item.icon, item.file_path) for item in tab_items)
            items.extend(tab_items)

        if self.tab_filt is not None:
            widget = self.tab_filt.widgets[0]
            assert isinstance(widget, QComboBox)
            widget.addItems(tab.get_tab_name() for tab in self.item_tabs)

        self.mod_db.insert_items(items)

        logger.info('Writing mod db file')
        with open(MOD_DB_FILE, 'wb') as f:
            pickle.dump(self.mod_db, f)

        download_manager.insert(
            thread.Call(download_manager.get_image, icon, None) for icon in icons
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
            lambda selected: self._update_tooltip(self.model, selected)
        )

        # Connect sort
        self.table.horizontalHeader().sortIndicatorChanged.connect(
            lambda logicalIndex, order: self.model.apply_filters(
                index=logicalIndex, order=order
            )
        )

        # Remaining resizing
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.resizeColumnsToContents()

    def _static_build(self) -> None:
        """Sets up the static base UI, including properties and widgets."""
        # Main Area
        main_hlayout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Area (Filters, Mods)
        self.left_widget = QWidget()
        left_vlayout = QVBoxLayout(self.left_widget)

        # Filters Group Box
        self.filter_group_box = QGroupBox()
        self.filter_group_box.setCheckable(True)
        filter_scroll_layout = QVBoxLayout(self.filter_group_box)
        filter_scroll_layout.setContentsMargins(0, 0, 0, 0)

        # Filters Scroll
        self.filter_scroll = QScrollArea()
        self.filter_scroll.setWidgetResizable(True)
        self.filter_scroll.setContentsMargins(0, 0, 0, 0)
        self.filter_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.filter_group_box.toggled.connect(
            lambda: _toggle_visibility(self.filter_scroll)
        )
        filter_scroll_layout.addWidget(self.filter_scroll)

        # Intermediate Filter Widget
        self.filter_scroll_widget = QWidget()
        self.filter_scroll.setWidget(self.filter_scroll_widget)
        self.filter_form_layout = QFormLayout()
        self.filter_vlayout = QVBoxLayout(self.filter_scroll_widget)
        self.filter_vlayout.addLayout(self.filter_form_layout)

        # Mods Group Box
        self.mods_group_box = QGroupBox()
        self.mods_group_box.setCheckable(True)
        mods_scroll_layout = QVBoxLayout(self.mods_group_box)
        mods_scroll_layout.setContentsMargins(0, 0, 0, 0)

        # Mods Scroll
        self.mods_scroll = QScrollArea()
        self.mods_scroll.setWidgetResizable(True)
        self.mods_scroll.setContentsMargins(0, 0, 0, 0)
        self.mods_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.mods_group_box.toggled.connect(
            lambda: _toggle_visibility(self.mods_scroll)
        )

        mods_scroll_layout.addWidget(self.mods_scroll)

        # Intermediate Mods Widget
        mods_scroll_widget = QWidget()
        self.mods_scroll.setWidget(mods_scroll_widget)
        self.mods_vlayout = QVBoxLayout(mods_scroll_widget)
        self.mods_vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        left_vlayout.addWidget(self.filter_group_box)
        left_vlayout.addWidget(self.mods_group_box)

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
        self.model = table.TableModel(self.table, parent=self)
        self.table.setModel(self.model)

        splitter.addWidget(self.left_widget)
        splitter.addWidget(self.tooltip)
        splitter.addWidget(self.table)
        splitter.setSizes((700, 700, 1000))

        main_hlayout.addWidget(splitter)

    def _load_mod_file(self) -> None:
        if os.path.isfile(MOD_DB_FILE):
            logger.info('Found mod db file')
            with open(MOD_DB_FILE, 'rb') as f:
                self.mod_db = pickle.load(f)
            assert isinstance(self.mod_db, moddb.ModDb)
            logger.info('Initial mods: %s', len(self.mod_db))

    def _build_individual_filter(
        self,
        filt: m_filter.Filter,
        form_layout: QFormLayout,
        index: int,
    ) -> None:
        """Builds an individual filter and inserts it into the UI."""
        # Create label
        label = QLabel(self.filter_scroll_widget)
        label.setText(filt.name)
        form_layout.setWidget(index, QFormLayout.ItemRole.LabelRole, label)

        # Create filter inputs
        layout = QHBoxLayout()
        num_widgets = len(inspect.signature(filt.filter_func).parameters) - 1
        for i in range(num_widgets):
            widget = filt.widget_type()
            widget.setSizePolicy(
                QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
            )
            filt.widgets.append(widget)
            layout.addWidget(widget)

            if isinstance(widget, QLineEdit):
                # Validator
                if filt.validator is not None:
                    widget.setValidator(filt.validator)

                # Placeholder text
                if num_widgets == 2:
                    widget.setPlaceholderText('min' if i == 0 else 'max')
                if num_widgets == 6:
                    text = {0: 'R', 1: 'G', 2: 'B', 3: 'W', 4: 'min', 5: 'max'}
                    widget.setPlaceholderText(text[i])

        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        form_layout.setLayout(index, QFormLayout.ItemRole.FieldRole, layout)

    def _build_regular_filters(self) -> QWidget:
        """Builds regular filter widgets (name, rarity, properties, etc)."""
        index = 0
        first_filt_widget: Optional[QWidget] = None
        for filt in m_filter.FILTERS:
            match filt:
                case m_filter.Filter():
                    self._build_individual_filter(filt, self.filter_form_layout, index)
                    if index == 0:
                        first_filt_widget = filt.widgets[0]
                    index += 1

                case m_filter.FilterGroup(group_name, filters, _):
                    # Filter group box
                    filt.group_box = QGroupBox(self.filter_scroll_widget)
                    filt.group_box.setTitle(group_name)
                    filt.group_box.setCheckable(True)
                    layout = QVBoxLayout(filt.group_box)
                    layout.setContentsMargins(0, 0, 0, 0)
                    widget = QWidget()
                    layout.addWidget(widget)
                    group_form = QFormLayout(widget)

                    def group_toggle(widget):
                        def f():
                            self._apply_filters()
                            _toggle_visibility(widget)

                        return f

                    filt.group_box.toggled.connect(group_toggle(widget))

                    self.filter_form_layout.setWidget(
                        index, QFormLayout.ItemRole.SpanningRole, filt.group_box
                    )
                    for i, ind_filter in enumerate(filters):
                        self._build_individual_filter(ind_filter, group_form, i)
                    index += 1

        assert first_filt_widget is not None
        return first_filt_widget

    def _build_mod_filters(self, first_filt_widget: QWidget) -> None:
        """Builds mod filter widgets."""
        range_size: Optional[QSize] = None
        for filt in m_filter.MOD_FILTERS:
            hlayout = QHBoxLayout()
            # Combo box
            widget = editcombo.ECBox()
            widget.setMinimumContentsLength(0)
            widget.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
            )
            widget.addItems(search for search in self.mod_db)
            widget.currentIndexChanged.connect(self._apply_filters)
            filt.widgets.append(widget)
            hlayout.addWidget(widget)

            # Range widgets
            for _ in range(2):
                range_widget = QLineEdit()
                if range_size is None:
                    range_height = first_filt_widget.sizeHint().height()
                    range_size = QSize((int)(range_height * 1.5), range_height)
                range_widget.setFixedSize(range_size)
                range_widget.textChanged.connect(self._apply_filters)
                range_widget.setValidator(QDoubleValidator())
                filt.widgets.append(range_widget)
                hlayout.addWidget(range_widget)
            self.mods_vlayout.addLayout(hlayout)

    def _dynamic_build_filters(self) -> None:
        """Sets up the filter widgets and labels."""
        first_filt_widget = self._build_regular_filters()
        self._build_mod_filters(first_filt_widget)

        # Resize left panel widths
        width = self.filter_group_box.sizeHint().width()
        self.filter_group_box.setMinimumWidth(width)
        self.mods_group_box.setMinimumWidth(width)

    def _name_ui(self) -> None:
        """Names the UI elements, including window title and labels."""
        self.filter_group_box.setTitle('Filters')
        self.mods_group_box.setTitle('Mods')

    def _update_tooltip(
        self, model: table.TableModel, selected: QItemSelection
    ) -> None:
        """Updates item tooltip, triggered when a row is clicked."""
        if not selected.indexes():
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
                    consts.SEPARATOR_TEMPLATE.format('assets/SeparatorWhite.png', width)
                )

        # Reset scroll to top
        self.tooltip.moveCursor(QTextCursor.MoveOperation.Start)

    def _apply_filters(self) -> None:
        """Function that applies filters."""
        self.model.apply_filters(index=1, order=Qt.SortOrder.AscendingOrder)

    def _connect_signal(self, filt: m_filter.Filter) -> None:
        """Connects apply filters function to when a filter's input changes."""
        for widget in filt.widgets:
            signal = None
            match widget:
                case QLineEdit():
                    signal = widget.textChanged
                case QComboBox():
                    signal = widget.currentIndexChanged
                case QCheckBox():
                    signal = widget.stateChanged
                case m_filter.InfluenceFilter():
                    signal = widget

            if signal is not None:
                signal.connect(self._apply_filters)

    def _setup_filters(self) -> None:
        """Initializes filters and links to widgets."""
        for filt in m_filter.FILTERS:
            match filt:
                case m_filter.Filter():
                    if filt.name == 'Tab':
                        self.tab_filt = filt
                    self._connect_signal(filt)
                    _populate_combo(filt)
                case m_filter.FilterGroup(_, filters, _):
                    for ind_filt in filters:
                        self._connect_signal(ind_filt)
                        _populate_combo(ind_filt)
