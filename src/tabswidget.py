from typing import TYPE_CHECKING

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

from save import Account, SavedData

if TYPE_CHECKING:
    from mainwindow import MainWindow


class TabsWidget(QWidget):
    """Widget for users to see and select stash tabs."""

    def __init__(self, mainWindow: 'MainWindow') -> None:
        """Initialize the UI."""
        QWidget.__init__(self)
        self.mainWindow = mainWindow
        self._staticBuild()
        self._dynamicBuild()
        self._nameUi()

    def onShow(self, savedData: SavedData, account: Account) -> None:
        self.savedData = savedData
        self.account = account
        if self.treeWidget.topLevelItemCount() != 0:
            return

        self._setupTree()

    def _staticBuild(self) -> None:
        """Setup the static base UI, including properties and widgets."""
        # Main area
        self.loginBox = QWidget(self)
        self.loginBox.setMinimumSize(QSize(500, 400))
        self.horizontalLayout = QHBoxLayout(self.loginBox)
        self.groupBox = QGroupBox()
        self.horizontalLayout.addWidget(self.groupBox)
        self.verticalLayout = QVBoxLayout(self.groupBox)

        # Tree Widget (for tabs)
        self.treeWidget = QTreeWidget()
        self.treeWidget.setHeaderHidden(True)
        self.verticalLayout.addWidget(self.treeWidget)

        # Error Text
        self.errorText = QLabel()
        self.errorText.setObjectName('ErrorText')
        self.verticalLayout.addWidget(self.errorText)

        # Buttons
        self.buttonLayout = QHBoxLayout()
        self.verticalLayout.addLayout(self.buttonLayout)

        # Back Button
        self.backButton = QPushButton()
        self.backButton.clicked.connect(
            lambda _: self.mainWindow.switchWidget(self.mainWindow.loginWidget)
        )
        self.buttonLayout.addWidget(self.backButton)

        # Import Button
        self.importButton = QPushButton()
        self.importButton.clicked.connect(
            lambda _: self.mainWindow.switchWidget(self.mainWindow.mainWidget)
        )
        self.buttonLayout.addWidget(self.importButton)

        self.mainHorizontalLayout = QHBoxLayout(self)
        self.mainHorizontalLayout.addWidget(
            self.loginBox, 0, Qt.AlignmentFlag.AlignCenter
        )

    def _dynamicBuild(self) -> None:
        pass

    def _setupTree(self):
        """Setup tabs in tree widget."""
        tabGroup = QTreeWidgetItem(self.treeWidget)
        tabGroup.setText(0, f'Stash Tabs ({self.account.tabsLength})')
        tabGroup.setFlags(
            tabGroup.flags()
            | Qt.ItemFlag.ItemIsAutoTristate
            | Qt.ItemFlag.ItemIsUserCheckable
        )
        tabGroup.setCheckState(0, Qt.CheckState.Checked)

        # Setup characters in tree widget
        charGroup = QTreeWidgetItem(self.treeWidget)
        charGroup.setText(0, f'Characters ({len(self.account.characterNames)})')
        charGroup.setFlags(tabGroup.flags())
        for char in self.account.characterNames:
            charWidget = QTreeWidgetItem(charGroup)
            charWidget.setText(0, char)
            charWidget.setFlags(charWidget.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            charWidget.setCheckState(0, Qt.CheckState.Checked)

    def _nameUi(self) -> None:
        """Name the UI elements, including window title and labels."""
        self.groupBox.setTitle('Select Tabs')
        self.backButton.setText('Back')
        self.importButton.setText('Import Tabs')
