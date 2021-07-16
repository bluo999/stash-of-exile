import json
import os
import pickle
import urllib.request

from http import HTTPStatus
from typing import Dict, List

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

URL_LEAGUES = 'https://api.pathofexile.com/leagues?type=main&compact=1'
HEADERS = {'User-Agent': 'stash_of_exile/0.1.0 (contact:brianluo999@gmail.com)'}

LEAGUES_FILE = '../leagues.pkl'


class LoginWidget(QWidget):
    """Widget for users to login"""

    def __init__(self, parent: QMainWindow) -> None:
        """Initialize the UI."""
        QWidget.__init__(self, parent)
        self._staticBuild()
        self._dynamicBuild()
        self._nameUi()

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

        # POESESSID Input
        self.poesessidLabel = QLabel()
        self.poesessidField = QLineEdit()
        self.poesessidField.setEchoMode(QLineEdit.EchoMode.Password)
        self.form.setWidget(0, QFormLayout.ItemRole.LabelRole, self.poesessidLabel)
        self.form.setWidget(0, QFormLayout.ItemRole.FieldRole, self.poesessidField)

        # League Combo Box
        self.leagueLabel = QLabel()
        self.leagueField = QComboBox()
        self.form.setWidget(1, QFormLayout.ItemRole.LabelRole, self.leagueLabel)
        self.form.setWidget(1, QFormLayout.ItemRole.FieldRole, self.leagueField)

        # Error Text
        self.errorText = QLabel()
        self.errorText.setObjectName('ErrorText')
        self.formVerticalLayout.addWidget(self.errorText)

        # Buttons
        self.buttonLayout = QHBoxLayout()
        self.formVerticalLayout.addLayout(self.buttonLayout)

        # League Button
        self.leagueButton = QPushButton()
        self.leagueButton.clicked.connect(self._getLeagues)  # type: ignore
        self.buttonLayout.addWidget(self.leagueButton)

        # Login Button
        self.loginButton = QPushButton()
        self.loginButton.setDisabled(True)
        self.loginButton.clicked.connect(self._login)  # type: ignore
        self.buttonLayout.addWidget(self.loginButton)

        self.mainHorizontalLayout = QHBoxLayout(self)
        self.mainHorizontalLayout.addWidget(
            self.loginBox, 0, Qt.AlignmentFlag.AlignCenter
        )

    def _dynamicBuild(self):
        """Setup leagues combo box if pickle is found."""
        if os.path.isfile(LEAGUES_FILE):
            print('Found leagues file')
            leagues = pickle.load(open(LEAGUES_FILE, 'rb'))
            self._getLeaguesSuccess(leagues)

    def _login(self):
        """Login with POESESSID."""
        self.parent().login()

    def _getLeagues(self):
        """Get leagues by sending a GET to Path of Exile API."""
        print('Sending GET request')
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
        self.poesessidLabel.setText('POESESSID: ')
        self.leagueLabel.setText('League: ')
        self.leagueButton.setText('Get Leagues')
        self.loginButton.setText('Login')
