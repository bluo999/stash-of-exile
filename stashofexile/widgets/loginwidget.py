"""
Handles league retrieving and login sequence.
"""

import os
import pickle

from typing import Any, Dict, List, Optional

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

from stashofexile import log, save
from stashofexile.threads import thread

mainwindow = Any

logger = log.get_logger(__name__)

SAVE_FILE = 'saveddata.pkl'


class LoginWidget(QWidget):
    """Widget for users to login"""

    def __init__(self, main_window: 'mainwindow.MainWindow') -> None:
        """Initialize the UI."""
        super().__init__()
        self.main_window = main_window
        self.saved_data = save.SavedData()
        self.account = None
        self.league = None
        self._static_build()
        self._dynamic_build()
        self._name_ui()

    def on_show(self, account: Optional[save.Account] = None) -> None:
        """Updates account if specified."""
        if account is not None:
            self.account = account

    def _dynamic_build(self) -> None:
        """Loads saved file and get leagues if necessary."""
        self._load_saved_file()
        if len(self.saved_data.leagues) == 0:
            self._get_leagues_api()
        else:
            self._get_leagues_success()

    def _static_build(self) -> None:
        """Sets up the static base UI, including properties and widgets."""
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
        """
        Loads existing save file. If none exists, then make a SavedData object.
        """
        if os.path.isfile(SAVE_FILE):
            logger.info('Found saved file')
            self.saved_data = pickle.load(open(SAVE_FILE, 'rb'))
            assert isinstance(self.saved_data, save.SavedData)
            logger.info(self.saved_data.leagues)
            for account in self.saved_data.accounts:
                logger.info('%s %s', account.username, account.poesessid)
            # Populatea user/poesessid
            # TODO: do by most recent
            if len(self.saved_data.accounts) > 0:
                account = self.saved_data.accounts[0]
                self.account_field.setText(self.saved_data.accounts[0].username)
                self.poesessid_field.setText(self.saved_data.accounts[0].poesessid)

    def _submit_cached(self) -> None:
        """Skips login and view cached stash."""
        self.main_window.switch_widget(self.main_window.main_widget)

    def _get_leagues_api(self) -> None:
        """Gets leagues from API."""
        logger.debug('Getting leagues')
        api_manager = self.main_window.api_manager
        api_manager.insert(
            [thread.Call(api_manager.get_leagues, (), self, self._get_leagues_callback)]
        )

    def _get_leagues_callback(
        self, leagues: Optional[List[str]], err_message: str = ''
    ) -> None:
        """Callback after get leagues is returned."""
        if leagues is None:
            logger.error(err_message)
            self.error_text.setText(err_message)
            return

        self.saved_data.leagues = leagues
        self._get_leagues_success()

    def _get_leagues_success(self) -> None:
        """Populates leagues combo box."""
        logger.info('Success: %s', self.saved_data.leagues)
        self.league_field.clear()
        self.league_field.addItems(self.saved_data.leagues)
        self.login_button.setEnabled(True)
        self.error_text.setText('')

    def _submit_login_info(self) -> None:
        """Submits login information: account name and POESESSID."""
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

        search_account = [
            savedAccount
            for savedAccount in self.saved_data.accounts
            if savedAccount.username == username
        ]

        if len(search_account) == 0:
            # Account not in saved data
            self.account = save.Account(username, poesessid)
            self.account.leagues[self.league] = save.League()
            self._get_char_list_api()
            self._get_num_tabs_api()
            return

        self.account = search_account[0]
        if self.league not in self.account.leagues.keys():
            self.account.leagues[self.league] = save.League()
            self._get_char_list_api()
            self._get_num_tabs_api()
            return

        account_league = self.account.leagues[self.league]
        if not account_league.has_characters():
            logger.info('Character list was not saved')
            self._get_char_list_api()
            return

        if self.account.poesessid != poesessid or not account_league.has_tabs():
            logger.info('POESESSID different or number of tabs was not saved')
            self.account.poesessid = poesessid
            self._get_num_tabs_api()
            return

        # Number of tabs and character list saved
        self._check_login_success()

    def _get_num_tabs_api(self) -> None:
        """Gets number of tabs from API."""
        assert self.account is not None
        assert self.league is not None
        logger.debug('Getting num tabs')
        api_manager = self.main_window.api_manager
        api_call = thread.Call(
            api_manager.get_tab_info,
            (self.account.username, self.account.poesessid, self.league),
            self,
            self._get_tab_info_callback,
        )
        api_manager.insert([api_call])

    def _get_tab_info_callback(
        self, tab_info: Optional[Dict[str, Any]], err_message: str = ''
    ) -> None:
        """Callback after get num tabs is returned."""
        if tab_info is None:
            logger.error(err_message)
            self.error_text.setText(err_message)
            return

        assert self.account is not None
        assert self.league is not None

        # Save username/poessesid to saved data
        if self.account not in self.saved_data.accounts:
            self.saved_data.accounts.append(self.account)

        tab_ids = [save.TabId(tab['n'], tab['id']) for tab in tab_info['tabs']]
        self.account.leagues[self.league].tab_ids = tab_ids
        logger.info('Success: %s tabs', len(tab_ids))
        self._check_login_success()

    def _get_char_list_api(self) -> None:
        """Gets character list from API."""
        assert self.account is not None
        assert self.league is not None
        logger.debug('Getting character list')
        api_manager = self.main_window.api_manager
        api_call = thread.Call(
            api_manager.get_character_list,
            (self.account.poesessid, self.league),
            self,
            self._get_char_list_callback,
        )
        api_manager.insert([api_call])

    def _get_char_list_callback(
        self, char_list: Optional[List[str]], err_message: str = ''
    ) -> None:
        """Callback after get num tabs is returned."""
        if char_list is None or len(char_list) == 0:
            if char_list is not None and len(char_list) == 0:
                err_message = 'Error getting characters. Are there any in that league?'
            logger.error(err_message)
            self.error_text.setText(err_message)
            return

        assert self.account is not None
        assert self.league is not None

        logger.info('Success: %s', char_list)
        self.account.leagues[self.league].character_names = char_list
        self.error_text.setText('')
        self._check_login_success()

    def _check_login_success(self) -> None:
        """
        Checks whether characters and tabs are set. If so, transition to tab widget.
        """
        assert self.account is not None
        assert self.league is not None
        account_league = self.account.leagues[self.league]
        if not account_league.has_characters() or not account_league.has_tabs():
            return

        # Switch to tab widget
        logger.info('Writing save file to %s', SAVE_FILE)
        pickle.dump(self.saved_data, open(SAVE_FILE, 'wb'))
        self.main_window.switch_widget(
            self.main_window.tabs_widget, self.saved_data, self.account, self.league
        )

    def _name_ui(self) -> None:
        """Names the UI elements, including window title and labels."""
        self.group_box.setTitle('Stash of Exile Login')
        self.account_label.setText('Account Name: ')
        self.poesessid_label.setText('POESESSID: ')
        self.league_label.setText('League: ')
        self.league_button.setText('Get Leagues')
        self.cached_button.setText('View Cached')
        self.login_button.setText('Login')
