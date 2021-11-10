"""
Handles creation of widgets, status bar, and some initial setup.
"""

import os

from typing import Callable, List, Tuple

from PyQt6 import QtGui
from PyQt6.QtCore import QRect
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QMenuBar, QStatusBar, QWidget

import log

from api import APIManager
from loginwidget import LoginWidget
from mainwidget import MainWidget
from tabswidget import TabsWidget

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
        self.api_manager.api_thread.output.connect(MainWindow.callback)

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
        """Switches to another widget and """
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
    def callback(cb_obj: QWidget, cb: Callable, cb_args: Tuple, args: Tuple) -> None:
        """Calls the callback function on an object with specified arguments."""
        logger.info(
            'Calling cb function %s %s (args(%s))', cb.__name__, cb_args, len(args)
        )
        getattr(cb_obj, cb.__name__)(*cb_args, *args)
