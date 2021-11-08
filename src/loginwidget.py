"""
Handles league retrieving and login sequence.
"""

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

SAVE_FILE = os.path.join('..', 'saveddata.pkl')


class LoginWidget(QWidget):
    """Widget for users to login"""

    def __init__(self, main_window: 'MainWindow') -> None:
        """Initialize the UI."""
        QWidget.__init__(self)
        self.main_window = main_window
        self.saved_data = None
        self.account = None
        self.league = None
        self._static_build()
        self._dynamic_build()
        self._name_ui()

    def on_show(
        self,
        saved_data: Union[SavedData, None] = None,
        account: Union[Account, None] = None,
    ) -> None:
        """Update saved data and account if specified."""
        if saved_data is not None:
            self.saved_data = saved_data
        if account is not None:
            self.account = account

    def _dynamic_build(self) -> None:
        """Load saved file and get leagues if necessary."""
        self._load_saved_file()
        assert self.saved_data is not None
        if len(self.saved_data.leagues) == 0:
            self._get_leagues_api()
        else:
            self._get_leagues_success()

    def _static_build(self) -> None:
        """Setup the static base UI, including properties and widgets."""
        # Main area
        self.login_box = QWidget(self)
        self.login_box.setMinimumSize(QSize(300, 200))
        self.hlayout = QHBoxLayout(self.login_box)
        self.group_box = QGroupBox()
        self.hlayout.addWidget(self.group_box)

        # Form
        self.form = QFormLayout()
        self.form_vlayout = QVBoxLayout(self.group_box)
        self.form_vlayout.addLayout(self.form)

        # Account name input
        self.account_label = QLabel()
        self.account_field = QLineEdit()
        self.form.setWidget(0, QFormLayout.ItemRole.LabelRole, self.account_label)
        self.form.setWidget(0, QFormLayout.ItemRole.FieldRole, self.account_field)

        # POESESSID Input
        self.poesessid_label = QLabel()
        self.poesessid_field = QLineEdit()
        self.poesessid_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.form.setWidget(1, QFormLayout.ItemRole.LabelRole, self.poesessid_label)
        self.form.setWidget(1, QFormLayout.ItemRole.FieldRole, self.poesessid_field)

        # League Combo Box
        self.league_label = QLabel()
        self.league_field = QComboBox()
        self.form.setWidget(2, QFormLayout.ItemRole.LabelRole, self.league_label)
        self.form.setWidget(2, QFormLayout.ItemRole.FieldRole, self.league_field)

        # Error Text
        self.error_text = QLabel()
        self.error_text.setObjectName('ErrorText')
        self.form_vlayout.addWidget(self.error_text)

        # League Button
        self.league_button = QPushButton()
        self.league_button.clicked.connect(self._get_leagues_api)
        self.form_vlayout.addWidget(self.league_button)

        # Buttons
        self.button_layout = QHBoxLayout()
        self.form_vlayout.addLayout(self.button_layout)

        # View Cached Button
        self.cached_button = QPushButton()
        self.cached_button.clicked.connect(self._submit_cached)
        self.button_layout.addWidget(self.cached_button)

        # Login Button
        self.login_button = QPushButton()
        self.login_button.setDisabled(True)
        self.login_button.clicked.connect(self._submit_login_info)
        self.button_layout.addWidget(self.login_button)

        self.main_hlayout = QHBoxLayout(self)
        self.main_hlayout.addWidget(self.login_box, 0, Qt.AlignmentFlag.AlignCenter)

    def _load_saved_file(self) -> None:
        """Load existing save file. If none exists,
        then make a SavedData object."""
        if os.path.isfile(SAVE_FILE):
            print('Found saved file')
            self.saved_data = pickle.load(open(SAVE_FILE, 'rb'))
            assert isinstance(self.saved_data, SavedData)
            print(self.saved_data.leagues)
            for account in self.saved_data.accounts:
                print(account.username, account.poesessid)
        else:
            self.saved_data = SavedData()

    def _get_leagues_api(self) -> None:
        """Get leagues from API."""
        assert self.saved_data is not None
        try:
            self.saved_data.leagues = APIManager.get_leagues()
            print(f'Success: {self.saved_data.leagues}')
        except HTTPError as e:
            self.error_text.setText(f'HTTP Error {e.code} {e.reason}')
            return
        except URLError as e:
            self.error_text.setText(f'URL Error {e.reason}')
            return

        # Success - leagues obtained
        self._get_leagues_success()

    def _get_leagues_success(self) -> None:
        """Populate leagues combo box."""
        self.league_field.clear()
        assert self.saved_data is not None
        self.league_field.addItems(self.saved_data.leagues)
        self.login_button.setEnabled(True)

    def _submit_cached(self) -> None:
        """Skip login and view cached stash."""
        self.main_window.switch_widget(self.main_window.main_widget)

    def _submit_login_info(self) -> None:
        """Submit login information: account name and POESESSID."""
        username = self.account_field.text()
        poesessid = self.poesessid_field.text()
        self.league = self.league_field.currentText()

        if len(username) == 0:
            self.error_text.setText('Account is blank')
            return

        if len(poesessid) == 0:
            self.error_text.setText('POESESSID is blank')
            return

        if len(self.league) == 0:
            self.error_text.setText('First get leagues')
            return

        assert self.saved_data is not None
        search_account = [
            savedAccount
            for savedAccount in self.saved_data.accounts
            if savedAccount.username == username
        ]

        if len(search_account) == 0:
            # Account not in saved data
            self.account = Account(username, poesessid)
            self.saved_data.accounts.append(self.account)
            self._get_num_tabs_api()
            return

        self.account = search_account[0]
        if self.account.poesessid != poesessid or self.account.tabs_length == 0:
            # POESESSID is different or number of tabs was not saved
            self.account.poesessid = poesessid
            self._get_num_tabs_api()
            return

        if len(self.account.character_names) == 0:
            # Character names were not saved
            self._get_char_list_api()
            return

        # Number of tabs and character list saved
        self._transition_tabs()

    def _get_num_tabs_api(self) -> None:
        """Get number of tabs from API."""
        assert self.account is not None
        assert self.league is not None
        try:
            self.account.tabs_length = APIManager.get_num_tabs(
                self.account.username, self.account.poesessid, self.league
            )
            print(f'Success: {self.account.tabs_length} tabs')
        except HTTPError as e:
            self.error_text.setText(f'HTTP Error {e.code} {e.reason}')
            return
        except URLError as e:
            self.error_text.setText(f'URL Error {e.reason}')
            return

        # Success - tabs obtained
        self._get_char_list_api()

    def _get_char_list_api(self) -> None:
        """Get character list from API."""
        assert self.account is not None
        assert self.league is not None
        try:
            self.account.character_names = APIManager.get_character_list(
                self.account.poesessid, self.league
            )
            print(f'Success: {self.account.character_names}')
        except HTTPError as e:
            self.error_text.setText(f'HTTP error {e.code} {e.reason}')
            return
        except URLError as e:
            self.error_text.setText(f'URL error {e.reason}')
            return

        # Success - character list obtained
        self._transition_tabs()

    def _transition_tabs(self) -> None:
        """Switch to tab widget."""
        print(f'Writing save file to {SAVE_FILE}')
        pickle.dump(self.saved_data, open(SAVE_FILE, 'wb'))
        self.main_window.switch_widget(
            self.main_window.tabs_widget, self.saved_data, self.account, self.league
        )

    def _http_error(self, code: int) -> None:
        pass

    def _name_ui(self) -> None:
        """Name the UI elements, including window title and labels."""
        self.group_box.setTitle('Stash of Exile Login')
        self.account_label.setText('Account Name: ')
        self.poesessid_label.setText('POESESSID: ')
        self.league_label.setText('League: ')
        self.league_button.setText('Get Leagues')
        self.cached_button.setText('View Cached')
        self.login_button.setText('Login')
