"""
Handles creation of widgets, status bar, and some initial setup.
"""

import os

from typing import List

from PyQt6 import QtGui
from PyQt6.QtCore import QRect
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QMenuBar, QStatusBar, QWidget

import log

from thread.api import APIManager
from thread.thread import Ret
from widgets.loginwidget import LoginWidget
from widgets.tabswidget import TabsWidget
from widgets.mainwidget import MainWidget

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

logger = log.get_logger(__name__)

# A font by Jos Buivenga (exljbris) -> www.exljbris.com
TTF_FILE = os.path.join('..', 'assets', 'FontinSmallCaps.ttf')


class MainWindow(QMainWindow):
    """Custom Main Window."""

    def __init__(self):
        QMainWindow.__init__(self)
        self.resize(1280, 720)
        self.setWindowTitle('Stash of Exile')

        QFontDatabase.addApplicationFont(TTF_FILE)

        # QSS file
        with open(os.path.join(__location__, 'styles.qss'), 'r') as f:
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
        self.api_manager = APIManager()
        self.api_manager.thread.output.connect(MainWindow.callback)

        # Initialize (and build) widgets
        self.login_widget = LoginWidget(self)
        self.tabs_widget = TabsWidget(self)
        self.main_widget = MainWidget(self)
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

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:  # pylint: disable=invalid-name
        """Kills the API thread on close."""
        self.api_manager.kill_thread()
        return super().closeEvent(a0)

    def switch_widget(self, dest_widget: QWidget, *args):
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

    @staticmethod
    def callback(api_ret: Ret) -> None:
        """Calls the callback function on an object with specified arguments."""
        logger.info(
            'Calling cb function %s %s (args(%s))',
            api_ret.cb.__name__,
            api_ret.cb_args,
            len(api_ret.service_result),
        )
        getattr(api_ret.cb_obj, api_ret.cb.__name__)(
            *api_ret.cb_args, *api_ret.service_result
        )