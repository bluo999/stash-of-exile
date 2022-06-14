"""
Handles viewing items in tabs and characters.
"""

import dataclasses
import functools
import inspect
import json
import os
import pickle
import re

from typing import Callable, List, TYPE_CHECKING, Optional, Set, Tuple

from PyQt6.QtCore import QItemSelection, QSize, Qt
from PyQt6.QtGui import QDoubleValidator, QFont, QTextCursor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from stashofexile import consts, file, gamedata, log, save, table
from stashofexile.items import (
    filter as m_filter,
    item as m_item,
    moddb,
    modfilter,
    tab as m_tab,
)
from stashofexile.threads import thread
from stashofexile.widgets import editcombo

if TYPE_CHECKING:
    from stashofexile import mainwindow

logger = log.get_logger(__name__)

MOD_DB_FILE = os.path.join(consts.APPDATA_DIR, 'mod_db.pkl')
ITEM_CACHE_DIR = os.path.join(consts.APPDATA_DIR, 'item_cache')

TABS_DIR = 'tabs'
CHARACTER_DIR = 'characters'
JEWELS_DIR = 'jewels'
UNIQUE_DIR = 'uniques'

UNIQUE_REGEX = re.compile(r'new R\((.*)\)\)\.run')


def _toggle_visibility(widget: QWidget) -> None:
    widget.setVisible(not widget.isVisible())


def _populate_combo(filt: m_filter.Filter) -> None:
    if (options := gamedata.COMBO_ITEMS.get(filt.name)) is not None:
        widget = filt.widgets[0]
        assert isinstance(widget, QComboBox)
        widget.addItems(options)


def _clear_layout(layout: QLayout) -> None:
    """Deletes all nested objects in a layout."""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        else:
            _clear_layout(item.layout())


class MainWidget(QWidget):
    """Main Widget for the filter, tooltip, and table view."""

    def __init__(self, main_window: 'mainwindow.MainWindow') -> None:
        """Initialize the UI."""
        super().__init__()
        self.main_window = main_window
        self.item_tabs: List[m_tab.ItemTab] = []
        self.account: Optional[save.Account] = None
        self.mod_db = moddb.ModDb()
        self.tab_filt: Optional[m_filter.Filter] = None
        self.range_size = QSize()
        self.reg_filters = m_filter.FILTERS.copy()
        self.mod_filters: List[modfilter.ModFilterGroup] = []
        self.pause_filter = False
        self._static_build()
        self._load_mod_file()
        self._dynamic_build_filters()
        self._setup_filters()
        self._name_ui()

    def on_show(  # pylint: disable=too-many-arguments, too-many-locals
        self,
        account: save.Account,
        league: str,
        tabs: List[int] = dataclasses.field(default_factory=list),
        characters: List[str] = dataclasses.field(default_factory=list),
        uniques: List[int] = dataclasses.field(default_factory=list),
        force_refresh: bool = False,
        cached: bool = False,
    ) -> None:
        """Sends API calls and builds the item table."""
        self.account = account
        self._send_api(league, tabs, characters, uniques, force_refresh, cached)
        self._build_table()

    def _send_api(  # pylint: disable=too-many-arguments
        self,
        league: str,
        tabs: List[int],
        characters: List[str],
        uniques: List[int],
        force_refresh: bool,
        cached: bool,
    ) -> None:
        assert self.account is not None
        if not force_refresh:
            logger.debug('Begin checking cache')

        api_manager = self.main_window.api_manager
        api_calls: List[thread.Call] = []

        # Queue stash tab API calls
        for tab_num in tabs:
            filename = os.path.join(
                ITEM_CACHE_DIR,
                self.account.username,
                league,
                TABS_DIR,
                f'{tab_num}.json',
            )
            item_tab = m_tab.StashTab(filename, tab_num)
            if not force_refresh and os.path.exists(filename):
                self.item_tabs.append(item_tab)
                continue
            if cached:
                continue
            api_call = thread.Call(
                api_manager.get_tab_items,
                (self.account.username, self.account.poesessid, league, tab_num),
                self,
                self._get_tab_callback,
                (item_tab,),
            )
            api_calls.append(api_call)

        # Queue character items API calls
        for char in characters:
            filename = os.path.join(
                ITEM_CACHE_DIR,
                self.account.username,
                league,
                CHARACTER_DIR,
                f'{char}.json',
            )
            item_tab = m_tab.CharacterTab(filename, char)
            if not force_refresh and os.path.exists(filename):
                self.item_tabs.append(item_tab)
                continue
            if cached:
                continue
            api_call = thread.Call(
                api_manager.get_character_items,
                (self.account.username, self.account.poesessid, char),
                self,
                self._get_tab_callback,
                (item_tab,),
            )
            api_calls.append(api_call)

        # Queue jewels API calls
        for char in characters:
            filename = os.path.join(
                ITEM_CACHE_DIR,
                self.account.username,
                league,
                JEWELS_DIR,
                f'{char}.json',
            )
            item_tab = m_tab.CharacterTab(filename, char)
            if not force_refresh and os.path.exists(filename):
                self.item_tabs.append(item_tab)
                continue
            if cached:
                continue
            api_call = thread.Call(
                api_manager.get_character_jewels,
                (self.account.username, self.account.poesessid, char),
                self,
                self._get_tab_callback,
                (item_tab,),
            )
            api_calls.append(api_call)

        # Queue unique tab API calls
        if self.account.leagues[league].uid:
            for unique in uniques:
                filename = os.path.join(
                    ITEM_CACHE_DIR,
                    self.account.username,
                    league,
                    UNIQUE_DIR,
                    f'{unique}.json',
                )
                item_tab = m_tab.UniqueSubTab(filename, unique)
                if not force_refresh and os.path.exists(filename):
                    self.item_tabs.append(item_tab)
                    continue
                if cached:
                    continue
                api_calls.append(
                    thread.Call(
                        api_manager.get_unique_subtab,
                        (
                            self.account.username,
                            self.account.leagues[league].uid,
                            unique,
                        ),
                        self,
                        self._get_unique_subtab_callback,
                        (item_tab,),
                    )
                )

        api_manager.insert(api_calls)

    def _on_receive_tab(self, tab: m_tab.ItemTab) -> None:
        items = tab.get_items()

        # Queue image downloading
        icons: Set[Tuple[str, str]] = set()
        download_manager = self.main_window.download_manager
        icons.update((item.icon, item.file_path) for item in items)
        download_manager.insert(
            thread.Call(download_manager.get_image, icon, None) for icon in icons
        )

        # Insert items into model
        self.model.insert_items(items)
        self._insert_mods(items)
        self._apply_filters()

        assert self.tab_filt is not None
        for widget in self.tab_filt.widgets:
            if isinstance(widget, editcombo.ECBox):
                widget.addItem(tab.get_tab_name())

    def _get_tab_callback(self, tab: m_tab.ItemTab, data, err_message: str) -> None:
        if data is None:
            # Use error message
            logger.warning(err_message)
            return

        logger.info('Writing item json to %s', tab.filepath)
        file.create_directories(tab.filepath)
        with open(tab.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        self.main_window.statusBar().showMessage(
            f'Items received: {tab.get_tab_name()}', consts.STATUS_TIMEOUT
        )
        self._on_receive_tab(tab)

    def _get_unique_subtab_callback(
        self, tab: m_tab.UniqueSubTab, js_code: str, err_message: str
    ) -> None:
        """Specific for unique subtab (since it uses JS code rather than direct JSON)."""
        if js_code is None:
            # Use error message
            logger.warning(err_message)
            return

        z = re.search(UNIQUE_REGEX, js_code)
        if z is None:
            logger.warning('Unexpected structure of return.')
            return

        logger.info('Writing subtab json to %s', tab.filepath)
        data = json.loads(z.groups()[0])
        json_data = {'items': [item_data[1] for item_data in data]}
        file.create_directories(tab.filepath)
        with open(tab.filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f)

        self.main_window.statusBar().showMessage(
            f'Unique subtab received: {tab.get_tab_name()}', consts.STATUS_TIMEOUT
        )
        self._on_receive_tab(tab)

    def _build_table(self) -> None:
        # Gets items and icons
        download_manager = self.main_window.download_manager
        items: List[m_item.Item] = []
        icons: Set[Tuple[str, str]] = set()
        for tab in self.item_tabs:
            tab_items = tab.get_items()
            icons.update((item.icon, item.file_path) for item in tab_items)
            items.extend(tab_items)

        # Add tab names to tab filter
        if self.tab_filt is not None:
            widget = self.tab_filt.widgets[0]
            assert isinstance(widget, QComboBox)
            # Remove duplicates
            names = dict.fromkeys(tab.get_tab_name() for tab in self.item_tabs)
            widget.addItems(names)

        self._insert_mods(items)

        # Download item icons
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

        # Connect selecting an item to update tooltip
        self.table.selectionModel().selectionChanged.connect(self._update_tooltip)

        # Connect property headers to sort
        self.table.horizontalHeader().sortIndicatorChanged.connect(
            lambda logicalIndex, order: self.model.apply_filters(
                self.reg_filters, self.mod_filters, index=logicalIndex, order=order
            )
        )

        # Remaining resizing
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.resizeColumnsToContents()

    def _static_build(self) -> None:
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

        # Plus Button
        plus_hlayout = QHBoxLayout()

        self.mod_combo = QComboBox()
        self.mod_combo.addItems(e.value for e in modfilter.ModFilterGroupType)
        plus_hlayout.addWidget(self.mod_combo)
        plus_hlayout.setAlignment(self.mod_combo, Qt.AlignmentFlag.AlignRight)

        plus_button = QPushButton()
        plus_button.setText('+')
        plus_button.setMaximumWidth(plus_button.sizeHint().height())
        plus_button.clicked.connect(self._add_mod_group)
        plus_hlayout.addWidget(plus_button)
        # plus_hlayout.setAlignment(plus_button, Qt.AlignmentFlag.AlignRight)
        self.mods_vlayout.addLayout(plus_hlayout)

        # Clear Filters Button
        self.clear_button = QPushButton()
        self.clear_button.clicked.connect(self._clear_all_filters)

        left_vlayout.addWidget(self.filter_group_box)
        left_vlayout.addWidget(self.mods_group_box)
        left_vlayout.addWidget(self.clear_button)

        # Middle scroll
        self.middle_widget = QWidget()
        middle_vlayout = QVBoxLayout(self.middle_widget)
        middle_vlayout.setSpacing(0)

        # Image
        self.image = QLabel()
        self.image.setFrameStyle(QFrame.Shape.NoFrame)
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image.setObjectName('Image')
        middle_vlayout.addWidget(self.image)

        # Tooltip
        self.tooltip = QTextEdit()
        self.tooltip.setFrameStyle(QFrame.Shape.NoFrame)
        self.tooltip.setReadOnly(True)
        self.tooltip.setFont(QFont('Fontin SmallCaps', 12))
        self.tooltip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tooltip.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tooltip.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        middle_vlayout.addWidget(self.tooltip)

        copy_button = QPushButton()
        copy_button.setText('Copy Item Text')
        middle_vlayout.addWidget(copy_button)
        copy_button.clicked.connect(self._copy_item_text)

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
        splitter.addWidget(self.middle_widget)
        splitter.addWidget(self.table)
        splitter.setSizes((700, 700, 700))

        main_hlayout.addWidget(splitter)

    def _group_toggle(self, widget: QWidget) -> Callable:
        def f():
            self._apply_filters()
            _toggle_visibility(widget)

        return f

    def _insert_mods(self, items):
        self.mod_db.insert_items(items)
        self.mod_db = moddb.ModDb(sorted(self.mod_db.items()))

        logger.info('Writing mod db file to %s', MOD_DB_FILE)
        with open(MOD_DB_FILE, 'wb') as f:
            pickle.dump(self.mod_db, f)

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

    def _build_filter_group_box(self, title: str) -> Tuple[QGroupBox, QWidget]:
        """Returns filter's group box and interior widget."""
        group_box = QGroupBox()
        group_box.setTitle(title)
        group_box.setCheckable(True)

        layout = QVBoxLayout(group_box)
        layout.setContentsMargins(0, 0, 0, 0)

        widget = QWidget()
        layout.addWidget(widget)
        group_box.toggled.connect(self._group_toggle(widget))

        return group_box, widget

    def _build_regular_filters(self) -> QWidget:
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
                    filt.group_box, widget = self._build_filter_group_box(group_name)
                    self.filter_form_layout.setWidget(
                        index, QFormLayout.ItemRole.SpanningRole, filt.group_box
                    )

                    group_form = QFormLayout(widget)
                    for i, ind_filter in enumerate(filters):
                        self._build_individual_filter(ind_filter, group_form, i)
                    index += 1

        assert first_filt_widget is not None
        return first_filt_widget

    def _add_mod_group(self) -> None:
        group = modfilter.ModFilterGroup(
            modfilter.ModFilterGroupType(self.mod_combo.currentText())
        )

        # Create mod filter group UI
        group.group_box, widget = self._build_filter_group_box(group.group_type.value)
        group.vlayout = QVBoxLayout(widget)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Insert QLineEdit for certain group types
        if group.group_type in (
            modfilter.ModFilterGroupType.COUNT,
            modfilter.ModFilterGroupType.WEIGHTED,
        ):
            group.min_lineedit = QLineEdit()
            group.min_lineedit.setValidator(QDoubleValidator())
            group.min_lineedit.setPlaceholderText('min')
            group.min_lineedit.textChanged.connect(self._apply_filters)
            button_layout.addWidget(group.min_lineedit)
            group.max_lineedit = QLineEdit()
            group.max_lineedit.setValidator(QDoubleValidator())
            group.max_lineedit.setPlaceholderText('max')
            group.max_lineedit.textChanged.connect(self._apply_filters)
            button_layout.addWidget(group.max_lineedit)

        # x and + buttons
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        plus_button = QPushButton()
        plus_button.setText('+')
        plus_button.setMaximumWidth(plus_button.sizeHint().height())
        button_layout.addWidget(plus_button)

        x_button = QPushButton()
        x_button.setText('x')
        x_button.setMaximumWidth(x_button.sizeHint().height())
        button_layout.addWidget(x_button)

        group.vlayout.addLayout(button_layout)

        # Connect signals
        weighted = group.group_type == modfilter.ModFilterGroupType.WEIGHTED
        plus_button.clicked.connect(
            functools.partial(self._add_mod_filter, group, weighted)
        )
        x_button.clicked.connect(functools.partial(self._delete_mod_group, group))

        # Finish adding group
        self.mod_filters.append(group)
        self.mods_vlayout.insertWidget(self.mods_vlayout.count() - 1, group.group_box)
        self._add_mod_filter(group, weighted)

    def _delete_mod_group(self, group: modfilter.ModFilterGroup) -> None:
        assert group.group_box is not None
        assert group.vlayout is not None
        self.mods_vlayout.removeWidget(group.group_box)
        _clear_layout(group.vlayout)
        group.vlayout.deleteLater()
        self.mod_filters.remove(group)
        self._apply_filters()

    def _add_mod_filter(
        self, group: modfilter.ModFilterGroup, weight: bool = False
    ) -> None:
        assert group.vlayout is not None

        hlayout = QHBoxLayout()
        filt = m_filter.Filter('', editcombo.ECBox, modfilter.filter_mod)
        group.filters.append(filt)

        # Combo box
        widget = editcombo.ECBox()
        widget.addItems(search for search in self.mod_db)
        widget.currentIndexChanged.connect(self._apply_filters)
        filt.widgets.append(widget)
        hlayout.addWidget(widget)

        # Range widgets
        num = 3 if weight else 2
        for i in range(num):
            range_widget = QLineEdit()
            range_widget.setFixedSize(self.range_size)
            range_widget.textChanged.connect(self._apply_filters)
            range_widget.setValidator(QDoubleValidator())
            range_widget.setPlaceholderText(
                'weight' if i == num - 3 else 'min' if i == num - 2 else 'max'
            )
            filt.widgets.append(range_widget)
            hlayout.addWidget(range_widget)

        x_button = QPushButton()
        x_button.setText('x')
        x_button.setMaximumWidth(x_button.sizeHint().height())
        x_button.clicked.connect(
            functools.partial(self._delete_mod_filter, hlayout, group, filt)
        )
        hlayout.addWidget(x_button)

        # Add layout to filter list
        group.vlayout.insertLayout(group.vlayout.count() - 1, hlayout)

    def _delete_mod_filter(
        self,
        filt_layout: QHBoxLayout,
        group: modfilter.ModFilterGroup,
        filt: m_filter.Filter,
    ) -> None:
        self.mods_vlayout.removeItem(filt_layout)
        _clear_layout(filt_layout)
        filt_layout.deleteLater()
        group.filters.remove(filt)
        self._apply_filters()

    def _clear_all_filters(self) -> None:
        # Pause filtering to prevent costly callbacks on resetting each field
        self.pause_filter = True

        for filt in self.reg_filters:
            match filt:
                case m_filter.Filter():
                    filt.clear_filter()
                case m_filter.FilterGroup(_, filters, _):
                    for ind_filter in filters:
                        ind_filter.clear_filter()

        while self.mod_filters:
            self._delete_mod_group(self.mod_filters[0])

        self.pause_filter = False
        self._apply_filters()

    def _dynamic_build_filters(self) -> None:
        first_filt_widget = self._build_regular_filters()
        range_height = first_filt_widget.sizeHint().height()
        self.range_size = QSize((int)(range_height * 1.5), range_height)

        # Resize left panel widths
        width = self.filter_group_box.sizeHint().width()
        self.filter_group_box.setMinimumWidth(width)
        self.mods_group_box.setMinimumWidth(width)

    def _name_ui(self) -> None:
        self.filter_group_box.setTitle('Filters')
        self.mods_group_box.setTitle('Mods')
        self.clear_button.setText('Clear Filters')

    def _copy_item_text(self) -> None:
        """Copies item text to clipboard."""
        if not self.table:
            return

        if not self.table.selectedIndexes():
            return

        row = self.table.selectedIndexes()[0].row()
        item = self.model.current_items[row]
        QApplication.clipboard().setText(item.get_text())

    def _update_tooltip(self, selected: QItemSelection) -> None:
        if not selected.indexes():
            # Nothing selected
            return

        row = selected.indexes()[0].row()
        item = self.model.current_items[row]

        # Update image
        self.image.setPixmap(item.get_image())

        # Update tooltip
        self.tooltip.setHtml('')
        sections = item.get_tooltip()
        width = self.tooltip.width() - self.tooltip.verticalScrollBar().width()

        # Construct tooltip from sections
        separator = os.path.join(
            consts.ASSETS_DIR,
            consts.FRAME_TYPES.get(item.rarity, consts.FRAME_TYPES['normal']),
        )
        for i, html in enumerate(sections):
            self.tooltip.append(html)
            self.tooltip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if i != len(sections) - 1:
                self.tooltip.append(consts.SEPARATOR_TEMPLATE.format(separator, width))

        # Reset scroll to top
        self.tooltip.moveCursor(QTextCursor.MoveOperation.Start)

    def _apply_filters(self) -> None:
        if self.pause_filter:
            return

        self.model.apply_filters(
            self.reg_filters,
            self.mod_filters,
        )

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
