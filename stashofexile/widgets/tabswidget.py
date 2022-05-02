"""
Defines a tab widget to select tabs and characters.
"""

import re
from typing import TYPE_CHECKING, Any, List, Optional

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from stashofexile import gamedata, log, save

if TYPE_CHECKING:
    from stashofexile import mainwindow

logger = log.get_logger(__name__)

UNIQUE_URL_REGEX = (
    r'https:\/\/www\.pathofexile\.com\/account\/view-stash\/.*\/(.*)(\/[0-9]+)'
)


class TabsWidget(QWidget):
    """Widget for users to see and select stash tabs."""

    def __init__(self, main_window: 'mainwindow.MainWindow') -> None:
        """Initialize the UI."""
        super().__init__()
        self.main_window = main_window
        self.saved_data: Optional[save.SavedData] = None
        self.account: Optional[save.Account] = None
        self.league: Optional[save.League] = None
        self._static_build()
        self._name_ui()

    def on_show(
        self, saved_data: save.SavedData, account: save.Account, league: str
    ) -> None:
        """Sets up tree based on saved_data and account."""
        self.saved_data = saved_data
        self.account = account
        self.league = league
        self.unique_label.setText(
            f'Enter unique tab URL for {self.league} league: (must be public)'
        )

        # TODO: clear tree then rebuild
        # Setup tree has not yet been called
        for _ in range(self.tab_group.childCount()):
            self.tab_group.removeChild(self.tab_group.child(0))
        for _ in range(self.char_group.childCount()):
            self.char_group.removeChild(self.char_group.child(0))
        for _ in range(self.unique_group.childCount()):
            self.unique_group.removeChild(self.unique_group.child(0))

        self._setup_tree()

    def _static_build(self) -> None:
        """Sets up the static base UI, including properties and widgets."""
        # Main area
        self.login_box = QWidget(self)
        self.login_box.setMinimumSize(QSize(500, 400))
        self.hlayout = QHBoxLayout(self.login_box)
        self.group_box = QGroupBox()
        self.hlayout.addWidget(self.group_box)
        self.vlayout = QVBoxLayout(self.group_box)

        # Tree Widget (for tabs)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.vlayout.addWidget(self.tree_widget)

        # Characters and Tabs
        self.tab_group = QTreeWidgetItem(self.tree_widget)
        self.char_group = QTreeWidgetItem(self.tree_widget)
        self.unique_group = QTreeWidgetItem(self.tree_widget)

        # Unique Tab Input
        self.unique_label = QLabel()
        self.unique_input = QLineEdit()
        self.vlayout.addWidget(self.unique_label)
        self.vlayout.addWidget(self.unique_input)

        # Error Text
        self.error_text = QLabel()
        self.error_text.setObjectName('ErrorText')
        self.vlayout.addWidget(self.error_text)

        # Buttons
        self.button_layout = QHBoxLayout()
        self.vlayout.addLayout(self.button_layout)

        # Back Button
        self.back_button = QPushButton()
        self.back_button.clicked.connect(
            lambda: self.main_window.switch_widget(self.main_window.login_widget)
        )
        # Not sure whether to remove or keep - maybe useful if selected wrong league?
        # self.back_button.setDisabled(True)
        self.button_layout.addWidget(self.back_button)

        # Import Button
        self.import_button = QPushButton()
        self.import_button.clicked.connect(self._import_items)
        self.button_layout.addWidget(self.import_button)

        self.main_hlayout = QHBoxLayout(self)
        self.main_hlayout.addWidget(self.login_box, 0, Qt.AlignmentFlag.AlignCenter)

    def _setup_tree(self):
        """Sets up tabs in tree widget."""
        assert self.account is not None
        assert self.league is not None
        account_league = self.account.leagues[self.league]
        self.tab_group.setText(0, f'Stash Tabs ({len(account_league.tab_ids)})')
        self.tab_group.setFlags(
            self.tab_group.flags()
            | Qt.ItemFlag.ItemIsAutoTristate
            | Qt.ItemFlag.ItemIsUserCheckable
        )
        for i, tab in enumerate(account_league.tab_ids):
            tab_widget = QTreeWidgetItem(self.tab_group)
            tab_widget.setText(0, f'{i} ({tab.name})')
            tab_widget.setFlags(tab_widget.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            tab_widget.setCheckState(0, Qt.CheckState.Checked)
        # self.tab_group.setCheckState(0, Qt.CheckState.Checked)

        # Setup characters in tree widget
        self.char_group.setText(
            0, f'Characters ({len(account_league.character_names)})'
        )
        self.char_group.setFlags(self.tab_group.flags())
        for char in account_league.character_names:
            char_widget = QTreeWidgetItem(self.char_group)
            char_widget.setText(0, char)
            char_widget.setFlags(char_widget.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            char_widget.setCheckState(0, Qt.CheckState.Checked)

        # Setup unique subtabs
        self.unique_group.setText(0, f'Unique Tab ({len(gamedata.UNIQUE_CATEGORIES)})')
        self.unique_group.setFlags(self.tab_group.flags())
        for cat in gamedata.UNIQUE_CATEGORIES.values():
            unique_widget = QTreeWidgetItem(self.unique_group)
            unique_widget.setText(0, cat)
            unique_widget.setFlags(
                unique_widget.flags() | Qt.ItemFlag.ItemIsUserCheckable
            )
            unique_widget.setCheckState(0, Qt.CheckState.Checked)

    def _import_items(self) -> None:
        """Sends the list of checked tabs and characters to the main widget."""
        assert self.account is not None
        assert self.league is not None
        # Get uid from URL
        text = self.unique_input.text()
        if text == '':
            uid = ''
        else:
            z = re.search(UNIQUE_URL_REGEX, text)
            if z is None:
                self.error_text.setText('Invalid unique URL')
                return
            uid = z.groups()[0]

        tabs = [
            i
            for i, _ in enumerate(self.account.leagues[self.league].tab_ids)
            if self.tab_group.child(i).checkState(0) == Qt.CheckState.Checked
        ]

        characters: List[str] = []
        for i in range(self.char_group.childCount()):
            char = self.char_group.child(i)
            if char.checkState(0) == Qt.CheckState.Checked:
                characters.append(char.text(0))

        keys = list(gamedata.UNIQUE_CATEGORIES)
        values = list(gamedata.UNIQUE_CATEGORIES.values())
        uniques: List[int] = []
        for i in range(self.unique_group.childCount()):
            unique = self.unique_group.child(i)
            if unique.checkState(0) == Qt.CheckState.Checked:
                uniques.append(keys[values.index(unique.text(0))])

        self.main_window.switch_widget(
            self.main_window.main_widget,
            self.account,
            self.league,
            tabs,
            characters,
            uniques,
            uid,
        )

    def _name_ui(self) -> None:
        """Names the UI elements, including window title and labels."""
        self.group_box.setTitle('Select Tabs')
        self.back_button.setText('Back')
        self.import_button.setText('Import Tabs')
