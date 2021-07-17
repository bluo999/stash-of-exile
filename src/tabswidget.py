from http import HTTPStatus
import json
import os
import pickle
import urllib.request

from functools import partial
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

from consts import HEADERS

if TYPE_CHECKING:
    from mainwindow import MainWindow


URL_TABS = (
    'https://pathofexile.com/character-window/get-stash-items?accountName={}&league={}'
)
URL_CHARACTERS = 'https://pathofexile.com/character-window/get-characters'

NUM_TABS_FILE = '../num_tabs.pkl'
CHARACTERS_FILE = '../characters.pkl'


class TabsWidget(QWidget):
    """Widget for users to see and select stash tabs."""

    def __init__(self, mainWindow: 'MainWindow') -> None:
        """Initialize the UI."""
        QWidget.__init__(self)
        self.mainWindow = mainWindow
        self._staticBuild()
        self._dynamicBuild()
        self._nameUi()

    def onShow(self, league, account, poesessid):
        if self.treeWidget.topLevelItemCount() == 0:
            self._importTabs(league, account, poesessid)

    def _staticBuild(self):
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

        # League Button
        self.backButton = QPushButton()
        self.backButton.clicked.connect(
            lambda _: self.mainWindow.switchWidget(self.mainWindow.loginWidget)
        )
        self.buttonLayout.addWidget(self.backButton)

        # Import Button
        self.importButton = QPushButton()
        self.importButton.setDisabled(True)
        self.importButton.clicked.connect(
            lambda _: self.mainWindow.switchWidget(self.mainWindow.mainWidget)
        )
        self.buttonLayout.addWidget(self.importButton)

        self.mainHorizontalLayout = QHBoxLayout(self)
        self.mainHorizontalLayout.addWidget(
            self.loginBox, 0, Qt.AlignmentFlag.AlignCenter
        )

    def _dynamicBuild(self):
        pass

    def _importTabs(self, league, account, poesessid):
        """Import number of tabs and character list."""
        # Get number of tabs
        if os.path.isfile(NUM_TABS_FILE):
            print('Found num tabs file')
            numTabs = pickle.load(open(NUM_TABS_FILE, 'rb'))
        else:
            print('Sending GET request for num tabs')
            req = urllib.request.Request(
                URL_TABS.format(account, league), headers=HEADERS
            )
            req.add_header('Cookie', f'POESESSID={poesessid}')
            r = urllib.request.urlopen(req)
            status = r.getcode()
            if status == HTTPStatus.OK:
                tabs = json.loads(r.read())
                numTabs = tabs['numTabs']
                pickle.dump(numTabs, open(NUM_TABS_FILE, 'wb'))
            else:
                self.errorText.setText(f'HTTP error {status}')
                return

        # Get character list
        if os.path.isfile(CHARACTERS_FILE):
            print('Found characters file')
            characters = pickle.load(open(CHARACTERS_FILE, 'rb'))
        else:
            print('Sending GET request for characters')
            req = urllib.request.Request(URL_CHARACTERS, headers=HEADERS)
            req.add_header('Cookie', f'POESESSID={poesessid}')
            r = urllib.request.urlopen(req)
            status = r.getcode()
            if status == HTTPStatus.OK:
                characters = json.loads(r.read())
                characters = [char for char in characters if char['league'] == league]
                pickle.dump(characters, open(CHARACTERS_FILE, 'wb'))
            else:
                self.errorText.set(f'HTTP error {status}')
                return

        self.importButton.setEnabled(True)
        self._setupTree(numTabs, characters)

    def _setupTree(self, numTabs, characters):
        # Setup tabs in tree widget
        tabGroup = QTreeWidgetItem(self.treeWidget)
        tabGroup.setText(0, f'Stash Tabs ({numTabs})')
        tabGroup.setFlags(
            tabGroup.flags()
            | Qt.ItemFlag.ItemIsAutoTristate
            | Qt.ItemFlag.ItemIsUserCheckable
        )
        tabGroup.setCheckState(0, Qt.CheckState.Checked)

        # Setup characters in tree widget
        charGroup = QTreeWidgetItem(self.treeWidget)
        charGroup.setText(0, f'Characters ({len(characters)})')
        charGroup.setFlags(tabGroup.flags())
        for char in characters:
            charWidget = QTreeWidgetItem(charGroup)
            charWidget.setText(0, char['name'])
            charWidget.setFlags(charWidget.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            charWidget.setCheckState(0, Qt.CheckState.Checked)

    def _nameUi(self) -> None:
        """Name the UI elements, including window title and labels."""
        self.groupBox.setTitle('Select Tabs')
        self.backButton.setText('Back')
        self.importButton.setText('Import Tabs')
