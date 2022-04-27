"""
Handles creation of widgets, status bar, and some initial setup.
"""

import os
import sys

from typing import List

from PyQt6 import QtGui
from PyQt6.QtCore import QRect
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QMenuBar, QStatusBar, QWidget

from stashofexile import consts, log
from stashofexile.threads import api, download, thread
from stashofexile.widgets import loginwidget, tabswidget, mainwidget

logger = log.get_logger(__name__)

# A font by Jos Buivenga (exljbris) -> www.exljbris.com
TTF_FILE = os.path.join('assets', 'FontinSmallCaps.ttf')

Widget = loginwidget.LoginWidget | mainwidget.MainWidget | tabswidget.TabsWidget


class MainWindow(QMainWindow):
    """Custom Main Window."""

    def __init__(self):
        super().__init__()
        self.resize(1280, 720)
        self.setWindowTitle('Stash of Exile')

        QFontDatabase.addApplicationFont(TTF_FILE)

        # QSS file
        with open('assets/styles.qss', 'r', encoding='utf-8') as f:
            self.setStyleSheet(f.read())

        # Menu bar
        menu_bar = QMenuBar(self)
        menu_bar.setGeometry(QRect(0, 0, 1280, 21))
        self.setMenuBar(menu_bar)

        # Status bar
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)

        # Screen widgets
        self.center_widget = QWidget(self)
        self.setCentralWidget(self.center_widget)
        self.central_layout = QHBoxLayout(self.center_widget)

        # Start API thread
        self.api_manager = api.APIManager()
        self.api_manager.thread.output.connect(MainWindow.callback)
        self.api_manager.thread.status_output.connect(self.update_status)

        # Start download thread
        self.download_manager = download.DownloadManager()

        # Initialize (and build) widgets
        self.login_widget = loginwidget.LoginWidget(self)
        self.tabs_widget = tabswidget.TabsWidget(self)
        self.main_widget = mainwidget.MainWidget(self)
        self.widgets: List[QWidget] = [
            self.login_widget,
            self.tabs_widget,
            self.main_widget,
        ]
        for widget in self.widgets:
            self.central_layout.addWidget(widget)

        self.switch_widget(self.login_widget)

        # Show window
        self.show()

    def closeEvent(  # pylint: disable=invalid-name,no-self-use
        self, _: QtGui.QCloseEvent
    ) -> None:
        """Exits the application."""
        logger.info('Main application exiting')
        sys.exit()

    def switch_widget(self, dest_widget: Widget, *args):
        """Switches to another widget."""
        assert dest_widget in self.widgets
        for widget in self.widgets:
            if widget == dest_widget:
                widget.setEnabled(True)
                widget.show()
            else:
                widget.setDisabled(True)
                widget.hide()

        dest_widget.on_show(*args)

    def update_status(self, message: str) -> None:
        """Updates the status bar message."""
        self.statusBar().showMessage(message, consts.STATUS_TIMEOUT)

    @staticmethod
    def callback(ret: thread.Ret) -> None:
        """Calls the callback function on an object with specified arguments."""
        if ret.cb_obj is None:
            return

        logger.info(
            'Calling cb function %s %s (args(%s))',
            ret.cb.__name__,
            ret.cb_args,
            len(ret.service_result),
        )
        getattr(ret.cb_obj, ret.cb.__name__)(*ret.cb_args, *ret.service_result)
