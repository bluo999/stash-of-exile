import os
import pickle
from urllib.error import HTTPError, URLError

from typing import TYPE_CHECKING, Union

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
from apimanager import APIManager

from save import Account, SavedData

if TYPE_CHECKING:
    from mainwindow import MainWindow

SAVE_FILE = '../saveddata.pkl'


class LoginWidget(QWidget):
    """Widget for users to login"""

    def __init__(self, mainWindow: 'MainWindow') -> None:
        """Initialize the UI."""
        QWidget.__init__(self)
        self.mainWindow = mainWindow
        self._staticBuild()
        self._dynamicBuild()
        self._nameUi()

    def onShow(
        self,
        savedData: Union[SavedData, None] = None,
        account: Union[Account, None] = None,
    ) -> None:
        if savedData is not None:
            self.savedData = savedData
        if account is not None:
            self.account = account

    def _dynamicBuild(self) -> None:
        """Load saved file and get leagues if necessary."""
        self._loadSavedFile()
        if len(self.savedData.leagues) == 0:
            self._getLeaguesAPI()
        else:
            self._getLeaguesSuccess()


    def _staticBuild(self) -> None:
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
        self.leagueButton.clicked.connect(self._getLeaguesAPI)
        self.buttonLayout.addWidget(self.leagueButton)

        # Login Button
        self.loginButton = QPushButton()
        self.loginButton.setDisabled(True)
        self.loginButton.clicked.connect(self._submitLoginInfo)
        self.buttonLayout.addWidget(self.loginButton)

        self.mainHorizontalLayout = QHBoxLayout(self)
        self.mainHorizontalLayout.addWidget(
            self.loginBox, 0, Qt.AlignmentFlag.AlignCenter
        )

    def _loadSavedFile(self) -> None:
        """Load existing save file. If none exists,
        then make a SavedData object."""
        if os.path.isfile(SAVE_FILE):
            print('Found saved file')
            self.savedData = pickle.load(open(SAVE_FILE, 'rb'))
            assert isinstance(self.savedData, SavedData)
        else:
            self.savedData = SavedData()

    def _getLeaguesAPI(self) -> None:
        """Get leagues from API."""
        try:
            self.savedData.leagues = APIManager.getLeagues()
            print(f'Success: {self.savedData.leagues}')
        except HTTPError as e:
            self.errorText.setText(f'HTTP Error {e.code}')
            return
        except URLError as e:
            self.errorText.setText(f'URL Error {e.reason}')
            return

        # Success - leagues obtained
        self._getLeaguesSuccess()

    def _getLeaguesSuccess(self) -> None:
        """Populate leagues combo box."""
        self.leagueField.clear()
        self.leagueField.addItems(self.savedData.leagues)
        self.loginButton.setEnabled(True)

    def _submitLoginInfo(self) -> None:
        """Submit login information: account name and POESESSID."""
        username = self.accountField.text()
        poesessid = self.poesessidField.text()
        self.league = self.leagueField.currentText()

        if len(username) == 0:
            self.errorText.setText('Account is blank')
            return

        if len(poesessid) == 0:
            self.errorText.setText('POESESSID is blank')
            return

        if len(self.league) == 0:
            self.errorText.setText('First get leagues')
            return

        searchAccount = [
            savedAccount
            for savedAccount in self.savedData.accounts
            if savedAccount.username == username
        ]

        if len(searchAccount) == 0:
            # Account not in saved data
            self.account = Account(username, poesessid)
            self.savedData.accounts.append(self.account)
            self._getNumTabsAPI()
            return

        self.account = searchAccount[0]
        if self.account.poesessid != poesessid or self.account.tabsLength == 0:
            # POESESSID is different or number of tabs was not saved
            self.account.poesessid = poesessid
            self._getNumTabsAPI()
            return

        if len(self.account.characterNames) == 0:
            # Character names were not saved
            self._getCharacterListAPI()
            return

        # Number of tabs and character list saved
        self._transitionTabs()

    def _getNumTabsAPI(self) -> None:
        """Get number of tabs from API."""
        try:
            self.account.tabsLength = APIManager.getNumTabs(self.account, self.league)
            print(f'Success: {self.account.tabsLength}')
        except HTTPError as e:
            self.errorText.setText(f'HTTP Error {e.code} {e.reason}')
            return
        except URLError as e:
            self.errorText.setText(f'URL Error {e.reason}')
            return

        # Success - tabs obtained
        self._getCharacterListAPI()

    def _getCharacterListAPI(self) -> None:
        """Get character list from API."""
        try:
            self.account.characterNames = APIManager.getCharacterList(
                self.account, self.league
            )
            print(f'Success: {self.account.characterNames}')
        except HTTPError as e:
            self.errorText.setText(f'HTTP error {e.code}')
            return
        except URLError as e:
            self.errorText.setText(f'URL error {e.reason}')
            return

        # Success - character list obtained
        self._transitionTabs()

    def _transitionTabs(self) -> None:
        """Switch to tab widget."""
        print(f'Writing save file to{SAVE_FILE}')
        pickle.dump(self.savedData, open(SAVE_FILE, 'wb'))
        self.mainWindow.switchWidget(
            self.mainWindow.tabsWidget, self.savedData, self.account
        )

    def _httpError(self, code: int) -> None:
        pass

    def _nameUi(self) -> None:
        """Name the UI elements, including window title and labels."""
        self.groupBox.setTitle('Stash of Exile Login')
        self.accountLabel.setText('Account Name: ')
        self.poesessidLabel.setText('POESESSID: ')
        self.leagueLabel.setText('League: ')
        self.leagueButton.setText('Get Leagues')
        self.loginButton.setText('Login')
