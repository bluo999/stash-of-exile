"""
Handles filtering of items.
"""

import functools
import inspect
import json
import os
import pickle
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import (QComboBox, QFormLayout, QFrame, QGroupBox,
                             QHBoxLayout, QInputDialog, QLabel, QLayout,
                             QLineEdit, QMessageBox, QPushButton, QScrollArea,
                             QSizePolicy, QTabWidget, QVBoxLayout, QWidget)

from stashofexile import consts, file, gamedata, log
from stashofexile.items import filter as m_filter
from stashofexile.items import item as m_item
from stashofexile.items import moddb, modfilter
from stashofexile.widgets import editcombo

if TYPE_CHECKING:
    from stashofexile.widgets import mainwidget

logger = log.get_logger(__name__)

MOD_DB_FILE = os.path.join(consts.APPDATA_DIR, 'mod_db.pkl')
PRESETS_DIR = os.path.join(consts.APPDATA_DIR, 'presets')


def _toggle_visibility(widget: QWidget) -> None:
    widget.setVisible(not widget.isVisible())


def _clear_layout(layout: QLayout) -> None:
    """Deletes all nested objects in a layout."""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        else:
            _clear_layout(item.layout())


def _delete_preset(widget: QWidget, layout: QLayout, filepath: str) -> None:
    _clear_layout(layout)
    widget.deleteLater()
    os.remove(filepath)


def _populate_combo(filt: m_filter.Filter) -> None:
    if (options := gamedata.COMBO_ITEMS.get(filt.name)) is not None:
        widget = filt.widgets[0]
        assert isinstance(widget, QComboBox)
        widget.addItems(options)


class FilterWidget(QWidget):
    """Widget for filtering options."""

    def __init__(self, main_widget: 'mainwidget.MainWidget') -> None:
        super().__init__()
        self.main = main_widget
        self.mod_db = moddb.ModDb()
        self.reg_filters = m_filter.FILTERS.copy()
        self.mod_filters: List[modfilter.ModFilterGroup] = []

        self._static_build()
        self._load_mod_file()
        self._dynamic_build_filters()
        self._build_presets()
        self._setup_filters()
        self._name_ui()

    def _static_build(self) -> None:
        left_vlayout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        left_vlayout.addWidget(self.tabs)

        # Filters Tab
        self.tab_filter = QWidget()
        self.tabs.addTab(self.tab_filter, 'Filters')
        filter_scroll_layout = QVBoxLayout(self.tab_filter)
        filter_scroll_layout.setContentsMargins(0, 0, 0, 0)

        self.filter_scroll = QScrollArea()
        self.filter_scroll.setWidgetResizable(True)
        self.filter_scroll.setContentsMargins(0, 0, 0, 0)
        self.filter_scroll.setFrameShape(QFrame.Shape.NoFrame)
        filter_scroll_layout.addWidget(self.filter_scroll)

        # Intermediate Filter Widget
        self.filter_scroll_widget = QWidget()
        self.filter_scroll.setWidget(self.filter_scroll_widget)
        self.filter_form_layout = QFormLayout()
        self.filter_vlayout = QVBoxLayout(self.filter_scroll_widget)
        self.filter_vlayout.addLayout(self.filter_form_layout)

        # Mods Tab
        self.tab_mod = QWidget()
        self.tabs.addTab(self.tab_mod, 'Mods')
        mods_scroll_layout = QVBoxLayout(self.tab_mod)
        mods_scroll_layout.setContentsMargins(0, 0, 0, 0)

        # Mods Scroll
        self.mods_scroll = QScrollArea()
        self.mods_scroll.setWidgetResizable(True)
        self.mods_scroll.setContentsMargins(0, 0, 0, 0)
        self.mods_scroll.setFrameShape(QFrame.Shape.NoFrame)
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
        plus_button.clicked.connect(
            lambda _: self._add_mod_group(
                modfilter.ModFilterGroupType(self.mod_combo.currentText())
            )
        )
        plus_hlayout.addWidget(plus_button)
        self.mods_vlayout.addLayout(plus_hlayout)

        # Preset Tab
        self.tab_preset = QWidget()
        self.tabs.addTab(self.tab_preset, 'Presets')
        preset_scroll_layout = QVBoxLayout(self.tab_preset)
        preset_scroll_layout.setContentsMargins(0, 0, 0, 0)

        # Preset Scroll
        self.preset_scroll = QScrollArea()
        self.preset_scroll.setWidgetResizable(True)
        self.preset_scroll.setContentsMargins(0, 0, 0, 0)
        self.preset_scroll.setFrameShape(QFrame.Shape.NoFrame)
        preset_scroll_layout.addWidget(self.preset_scroll)

        # Intermediate Preset Widget
        preset_scroll_widget = QWidget()
        self.preset_scroll.setWidget(preset_scroll_widget)
        self.preset_vlayout = QVBoxLayout(preset_scroll_widget)
        self.preset_vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Bottom Buttons
        self.clear_button = QPushButton()
        self.clear_button.clicked.connect(lambda _: self._clear_all_filters(True))

        self.save_button = QPushButton()
        self.save_button.clicked.connect(self._save_filter)

        left_vlayout.addWidget(self.clear_button)
        left_vlayout.addWidget(self.save_button)

    def _name_ui(self) -> None:
        self.clear_button.setText('Clear Filters')
        self.save_button.setText('Save Current Filter')

    def _group_toggle(self, widget: QWidget) -> Callable:
        def f():
            self.main.apply_filters()
            _toggle_visibility(widget)

        return f

    def _load_mod_file(self) -> None:
        if os.path.isfile(MOD_DB_FILE):
            logger.info('Found mod db file')
            with open(MOD_DB_FILE, 'rb') as f:
                self.mod_db = pickle.load(f)
            assert isinstance(self.mod_db, moddb.ModDb)
            logger.info('Initial mods: %s', len(self.mod_db))

    def _dynamic_build_filters(self) -> None:
        first_filt_widget = self._build_regular_filters()
        range_height = first_filt_widget.sizeHint().height()
        self.range_size = QSize((int)(range_height * 1.5), range_height)

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

    def _clear_all_filters(self, refresh=True) -> None:
        # Pause filtering to prevent costly callbacks on resetting each field
        self.main.pause_updates(True)

        for filt in self.reg_filters:
            match filt:
                case m_filter.Filter():
                    filt.clear_filter()
                case m_filter.FilterGroup():
                    filt.clear_filter()

        while self.mod_filters:
            self._delete_mod_group(self.mod_filters[0])

        self.main.pause_updates(False)
        if refresh:
            self.main.apply_filters()

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
        widget.currentIndexChanged.connect(self.main.apply_filters)
        filt.widgets.append(widget)
        hlayout.addWidget(widget)

        # Range widgets
        num = 3 if weight else 2
        for i in range(num):
            range_widget = QLineEdit()
            range_widget.setFixedSize(self.range_size)
            range_widget.textChanged.connect(self.main.apply_filters)
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

    def _add_mod_group(
        self, group_type: modfilter.ModFilterGroupType, blank=True
    ) -> None:
        group = modfilter.ModFilterGroup(group_type)

        # Create mod filter group UI
        group.group_box, widget = self._build_filter_group_box(group_type.value)
        group.vlayout = QVBoxLayout(widget)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Insert QLineEdit for certain group types
        if group_type in (
            modfilter.ModFilterGroupType.COUNT,
            modfilter.ModFilterGroupType.WEIGHTED,
        ):
            group.min_lineedit = QLineEdit()
            group.min_lineedit.setValidator(QDoubleValidator())
            group.min_lineedit.setPlaceholderText('min')
            group.min_lineedit.textChanged.connect(self.main.apply_filters)
            button_layout.addWidget(group.min_lineedit)
            group.max_lineedit = QLineEdit()
            group.max_lineedit.setValidator(QDoubleValidator())
            group.max_lineedit.setPlaceholderText('max')
            group.max_lineedit.textChanged.connect(self.main.apply_filters)
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
        weighted = group_type == modfilter.ModFilterGroupType.WEIGHTED
        plus_button.clicked.connect(
            functools.partial(self._add_mod_filter, group, weighted)
        )
        x_button.clicked.connect(functools.partial(self._delete_mod_group, group))

        # Finish adding group
        self.mod_filters.append(group)
        self.mods_vlayout.insertWidget(self.mods_vlayout.count() - 1, group.group_box)

        if blank:
            self._add_mod_filter(group, weighted)

    def _delete_mod_group(self, group: modfilter.ModFilterGroup) -> None:
        assert group.group_box is not None
        assert group.vlayout is not None
        self.mods_vlayout.removeWidget(group.group_box)
        _clear_layout(group.vlayout)
        group.vlayout.deleteLater()
        self.mod_filters.remove(group)
        self.main.apply_filters()

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
        self.main.apply_filters()

    def _load_preset(self, filepath: str) -> None:
        self._clear_all_filters(False)
        self.main.pause_updates(True)

        with open(filepath, 'rb') as f:
            preset = json.load(f)

        filter_data = preset['filters']
        for filt in self.reg_filters:
            match filt:
                case m_filter.Filter():
                    filt.set_values(filter_data.get(filt.name, []))
                case m_filter.FilterGroup():
                    filt.set_values(filter_data.get(filt.name, {}))

        for group_data in preset['mod_groups']:
            group_type = modfilter.ModFilterGroupType(group_data['group_type'])
            self._add_mod_group(group_type, False)
            mod_group = self.mod_filters[-1]
            if mod_group.min_lineedit:
                mod_group.min_lineedit.setText(group_data.get('min', ''))
            if mod_group.max_lineedit:
                mod_group.max_lineedit.setText(group_data.get('max', ''))

            for mods_data in group_data['mods']:
                self._add_mod_filter(
                    mod_group,
                    group_type == modfilter.ModFilterGroupType.WEIGHTED,
                )
                widgets = mod_group.filters[-1].widgets

                ecbox = widgets[0]
                assert isinstance(ecbox, editcombo.ECBox)
                ecbox.setCurrentIndex(ecbox.findText(mods_data[0]))

                for val, widget in zip(mods_data[1:], widgets[1:]):
                    assert isinstance(widget, QLineEdit)
                    if val:
                        widget.setText(val)

        self.main.pause_updates(False)
        self.main.apply_filters()

    def _export_preset(self, name: str, filename: str) -> None:
        data = {}
        data['name'] = name
        data['filters'] = {}
        for filt in self.reg_filters:
            match filt:
                case m_filter.Filter(name, _):
                    if val := filt.to_json():
                        data['filters'][name] = val
                case m_filter.FilterGroup(name, _):
                    if val := filt.to_json():
                        data['filters'][name] = val

        data['mod_groups'] = [mod_group.to_json() for mod_group in self.mod_filters]

        filepath = os.path.join(PRESETS_DIR, f'{filename}.json')
        file.create_directories(filepath)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        self._build_preset(filepath)

    def _save_filter(self) -> None:
        name, ok = QInputDialog.getText(self, 'Input', 'Enter filter name:')

        if ok and name:
            self._export_preset(name, name)

    def _build_preset(self, filepath: str) -> None:
        widget = QWidget()
        hlayout = QHBoxLayout(widget)
        label = QLabel(file.get_file_name(filepath))
        hlayout.addWidget(label)

        button = QPushButton('Load')
        button.setFixedSize(self.range_size)
        button.clicked.connect(functools.partial(self._load_preset, filepath))
        hlayout.addWidget(button)
        button = QPushButton('Delete')
        button.setFixedSize(self.range_size)
        button.clicked.connect(
            functools.partial(self._confirm_delete_preset, widget, hlayout, filepath)
        )
        hlayout.addWidget(button)

        hlayout.setContentsMargins(0, 0, 0, 0)
        self.preset_vlayout.addWidget(widget)

    def _build_presets(self) -> None:
        jsons = file.get_jsons(PRESETS_DIR)
        if not jsons:
            return

        for filepath in jsons:
            self._build_preset(filepath)

    def _confirm_delete_preset(
        self, widget: QWidget, layout: QLayout, filepath: str
    ) -> None:
        confirm = QMessageBox.question(
            self,
            'Confirm',
            'Delete preset?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            _delete_preset(widget, layout, filepath)

    def _connect_signal(self, filt: m_filter.Filter) -> None:
        """Connects apply filters function to when a filter's input changes."""
        for widget in filt.widgets:
            signal = None
            match widget:
                case QLineEdit():
                    signal = widget.textChanged
                case QComboBox():
                    signal = widget.currentIndexChanged
                case m_filter.InfluenceFilter():
                    signal = widget

            if signal is not None:
                signal.connect(self.main.apply_filters)

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

    def insert_mods(self, items: List[m_item.Item]):
        """Inserts mods into the database."""
        self.mod_db.insert_items(items)
        self.mod_db = moddb.ModDb(sorted(self.mod_db.items()))

        logger.info('Writing mod db file to %s', MOD_DB_FILE)
        with open(MOD_DB_FILE, 'wb') as f:
            pickle.dump(self.mod_db, f)
