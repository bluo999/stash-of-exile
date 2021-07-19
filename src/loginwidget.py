import json
import os
import pickle
import urllib.request

from http import HTTPStatus
from typing import Dict, List, TYPE_CHECKING

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from consts import HEADERS

if TYPE_CHECKING:
    from mainwindow import MainWindow


URL_LEAGUES = 'https://api.pathofexile.com/leagues?type=main&compact=1'

LEAGUES_FILE = '../leagues.pkl'


class LoginWidget(QWidget):
    """Widget for users to login"""

    def __init__(self, mainWindow: 'MainWindow') -> None:
        """Initialize the UI."""
        QWidget.__init__(self)
        self.mainWindow = mainWindow
        self._staticBuild()
        self._dynamicBuild()
        self._nameUi()

    def onShow(self):
        pass

    def _staticBuild(self):
        """Setup the static base UI, including properties and widgets."""
        # Main area
        self.loginBox = QWidget(self)
        self.loginBox.setMinimumSize(QSize(300, 200))
        self.horizontalLayout = QHBoxLayout(self.loginBox)
        self.groupBox = QGroupBox()
        self.horizontalLayout.addWidget(self.groupBox)

        # Form
        self.form = QFormLayout()
        self.formVerticalLayout = QVBoxLayout(self.groupBox)
        self.formVerticalLayout.addLayout(self.form)

        # Account name input
        self.accountLabel = QLabel()
        self.accountField = QLineEdit()
        self.form.setWidget(0, QFormLayout.ItemRole.LabelRole, self.accountLabel)
        self.form.setWidget(0, QFormLayout.ItemRole.FieldRole, self.accountField)

        # POESESSID Input
        self.poesessidLabel = QLabel()
        self.poesessidField = QLineEdit()
        self.poesessidField.setEchoMode(QLineEdit.EchoMode.Password)
        self.form.setWidget(1, QFormLayout.ItemRole.LabelRole, self.poesessidLabel)
        self.form.setWidget(1, QFormLayout.ItemRole.FieldRole, self.poesessidField)

        # League Combo Box
        self.leagueLabel = QLabel()
        self.leagueField = QComboBox()
        self.form.setWidget(2, QFormLayout.ItemRole.LabelRole, self.leagueLabel)
        self.form.setWidget(2, QFormLayout.ItemRole.FieldRole, self.leagueField)

        # Error Text
        self.errorText = QLabel()
        self.errorText.setObjectName('ErrorText')
        self.formVerticalLayout.addWidget(self.errorText)

        # Buttons
        self.buttonLayout = QHBoxLayout()
        self.formVerticalLayout.addLayout(self.buttonLayout)

        # League Button
        self.leagueButton = QPushButton()
        self.leagueButton.clicked.connect(self._getLeagues)
        self.buttonLayout.addWidget(self.leagueButton)

        # Login Button
        self.loginButton = QPushButton()
        self.loginButton.setDisabled(True)
        self.loginButton.clicked.connect(self._login)
        self.buttonLayout.addWidget(self.loginButton)

        self.mainHorizontalLayout = QHBoxLayout(self)
        self.mainHorizontalLayout.addWidget(
            self.loginBox, 0, Qt.AlignmentFlag.AlignCenter
        )

    def _dynamicBuild(self):
        self._getLeagues()

    def _login(self):
        """Login with account name and POESESSID."""
        account = self.accountField.text()
        poesessid = self.poesessidField.text()
        league = self.leagueField.currentText()

        if len(account) == 0:
            self.errorText.setText('Account is blank')
            return

        if len(poesessid) == 0:
            self.errorText.setText('POESESSID is blank')
            return

        if len(league) == 0:
            self.errorText.setText('First get leagues')

        self.mainWindow.switchWidget(
            self.mainWindow.tabsWidget, league, account, poesessid
        )

    def _getLeagues(self):
        """Get leagues by sending a GET to Path of Exile API."""
        if self.leagueField.count() > 0:
            return

        if os.path.isfile(LEAGUES_FILE):
            print('Found leagues file')
            leagues = pickle.load(open(LEAGUES_FILE, 'rb'))
            self._getLeaguesSuccess(leagues)
        else:
            print('Sending GET request for leagues')
            req = urllib.request.Request(URL_LEAGUES, headers=HEADERS)
            r = urllib.request.urlopen(req)
            status = r.getcode()
            if status == HTTPStatus.OK:
                leagues = json.loads(r.read())
                pickle.dump(leagues, open(LEAGUES_FILE, 'wb'))
                self._getLeaguesSuccess(leagues)
            else:
                self.errorText.setText(f'HTTP error {status}')

    def _getLeaguesSuccess(self, leagues: List[Dict[str, str]]):
        """Populate leagues combo box given JSON."""
        self.leagueField.addItems(league['id'] for league in leagues)
        self.loginButton.setEnabled(True)

    def _nameUi(self) -> None:
        """Name the UI elements, including window title and labels."""
        self.groupBox.setTitle('Stash of Exile Login')
        self.accountLabel.setText('Account Name: ')
        self.poesessidLabel.setText('POESESSID: ')
        self.leagueLabel.setText('League: ')
        self.leagueButton.setText('Get Leagues')
        self.loginButton.setText('Login')
