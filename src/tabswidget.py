"""
Defines a tab widget to select tabs and characters.
"""

from typing import TYPE_CHECKING, List

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

import log

from save import Account, SavedData

if TYPE_CHECKING:
    from mainwindow import MainWindow

logger = log.get_logger(__name__)


class TabsWidget(QWidget):
    """Widget for users to see and select stash tabs."""

    def __init__(self, main_window: 'MainWindow') -> None:
        """Initialize the UI."""
        QWidget.__init__(self)
        self.main_window = main_window
        self.saved_data = None
        self.account = None
        self.league = None
        self._static_build()
        self._name_ui()

    def on_show(self, saved_data: SavedData, account: Account, league: str) -> None:
        """Setup tree based on saved_data and account."""
        self.saved_data = saved_data
        self.account = account
        self.league = league

        # TODO: clear tree then rebuild
        # Setup tree has not yet been called
        if self.tree_widget.topLevelItemCount() == 2:
            self._setup_tree()

    def _static_build(self) -> None:
        """Setup the static base UI, including properties and widgets."""
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
            lambda _: self.main_window.switch_widget(self.main_window.login_widget)
        )
        # Not sure whether to remove or keep - maybe useful if selected wrong league?
        self.back_button.setDisabled(True)
        self.button_layout.addWidget(self.back_button)

        # Import Button
        self.import_button = QPushButton()
        self.import_button.clicked.connect(self._import_items)
        self.button_layout.addWidget(self.import_button)

        self.main_hlayout = QHBoxLayout(self)
        self.main_hlayout.addWidget(self.login_box, 0, Qt.AlignmentFlag.AlignCenter)

    def _setup_tree(self):
        """Setup tabs in tree widget."""
        assert self.account is not None
        self.tab_group.setText(0, f'Stash Tabs ({len(self.account.tab_ids)})')
        self.tab_group.setFlags(
            self.tab_group.flags()
            | Qt.ItemFlag.ItemIsAutoTristate
            | Qt.ItemFlag.ItemIsUserCheckable
        )
        for i, tab in enumerate(self.account.tab_ids):
            tab_widget = QTreeWidgetItem(self.tab_group)
            tab_widget.setText(0, f'{i} ({tab.name})')
            tab_widget.setFlags(tab_widget.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            tab_widget.setCheckState(0, Qt.CheckState.Checked)
        # self.tab_group.setCheckState(0, Qt.CheckState.Checked)

        # Setup characters in tree widget
        self.char_group.setText(0, f'Characters ({len(self.account.character_names)})')
        self.char_group.setFlags(self.tab_group.flags())
        for char in self.account.character_names:
            char_widget = QTreeWidgetItem(self.char_group)
            char_widget.setText(0, char)
            char_widget.setFlags(char_widget.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            char_widget.setCheckState(0, Qt.CheckState.Checked)

    def _import_items(self) -> None:
        """Send the list of checked tabs and characters to the main widget."""
        assert self.account is not None
        logger.debug('Getting checked')
        tabs = [
            i
            for i, _ in enumerate(self.account.tab_ids)
            if self.tab_group.child(i).checkState(0) == Qt.CheckState.Checked
        ]

        characters: List[str] = []
        for i in range(self.char_group.childCount()):
            char = self.char_group.child(i)
            if char.checkState(0) == Qt.CheckState.Checked:
                characters.append(char.text(0))

        logger.debug('Finished checked')

        self.main_window.switch_widget(
            self.main_window.main_widget, self.account, self.league, tabs, characters
        )

    def _name_ui(self) -> None:
        """Name the UI elements, including window title and labels."""
        self.group_box.setTitle('Select Tabs')
        self.back_button.setText('Back')
        self.import_button.setText('Import Tabs')
