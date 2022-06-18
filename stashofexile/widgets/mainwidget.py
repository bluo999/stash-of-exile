"""
Handles viewing items in tabs and characters.
"""

import dataclasses
import json
import os
import re

from typing import List, TYPE_CHECKING, Optional, Set, Tuple

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QSplitter,
    QTableView,
    QWidget,
)

from stashofexile import consts, file, log, save, table
from stashofexile.items import (
    filter as m_filter,
    item as m_item,
    tab as m_tab,
)
from stashofexile.threads import thread
from stashofexile.widgets import editcombo, filterwidget
from stashofexile.widgets import tooltipwidget

if TYPE_CHECKING:
    from stashofexile import mainwindow

logger = log.get_logger(__name__)

ITEM_CACHE_DIR = os.path.join(consts.APPDATA_DIR, 'item_cache')

TABS_DIR = 'tabs'
CHARACTER_DIR = 'characters'
JEWELS_DIR = 'jewels'
UNIQUE_DIR = 'uniques'

UNIQUE_REGEX = re.compile(r'new R\((.*)\)\)\.run')


class MainWidget(QWidget):
    """Main Widget for the filter, tooltip, and table view."""

    def __init__(self, main_window: 'mainwindow.MainWindow') -> None:
        """Initialize the UI."""
        super().__init__()
        self.main_window = main_window
        self.item_tabs: List[m_tab.ItemTab] = []
        self.account: Optional[save.Account] = None
        self.tab_filt: Optional[m_filter.Filter] = None
        self.range_size = QSize()
        self.pause_filter = False
        self._static_build()

    def _static_build(self) -> None:
        # Main Area
        main_hlayout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_hlayout.addWidget(splitter)

        self.filter_widget = filterwidget.FilterWidget(self)
        self.tooltip_widget = tooltipwidget.TooltipWidget(self)
        self._build_right()

        splitter.addWidget(self.filter_widget)
        splitter.addWidget(self.tooltip_widget)
        splitter.addWidget(self.table)
        splitter.setSizes((700, 700, 700))

    def _build_right(self) -> None:
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

        self.filter_widget.insert_mods(items)

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
        self.table.selectionModel().selectionChanged.connect(
            self.tooltip_widget.update_tooltip
        )

        # Connect property headers to sort
        self.table.horizontalHeader().sortIndicatorChanged.connect(
            lambda logicalIndex, order: self.model.apply_filters(
                self.filter_widget.reg_filters,
                self.filter_widget.mod_filters,
                index=logicalIndex,
                order=order,
            )
        )

        # Remaining resizing
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.resizeColumnsToContents()

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
        self.filter_widget.insert_mods(items)
        self.apply_filters()

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

    def apply_filters(self) -> None:
        """Applies filters to the table model."""
        if self.pause_filter:
            return

        self.model.apply_filters(
            self.filter_widget.reg_filters,
            self.filter_widget.mod_filters,
        )

    def pause_updates(self, pause: bool) -> None:
        """Pauses or unpauses updating table based on the filter."""
        self.pause_filter = pause
