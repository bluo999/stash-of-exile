"""
Handles creation of widgets, status bar, and some initial setup.
"""

import os
import sys
from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QFontDatabase
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from stashofexile import consts, log
from stashofexile.threads import api, download, thread
from stashofexile.widgets import loginwidget, mainwidget, tabswidget

logger = log.get_logger(__name__)

# A font by Jos Buivenga (exljbris) -> www.exljbris.com
TTF_FILE = os.path.join(consts.ASSETS_DIR, 'FontinSmallCaps.ttf')
QSS_FILE = os.path.join(consts.ASSETS_DIR, 'styles.qss')

Widget = loginwidget.LoginWidget | mainwidget.MainWidget | tabswidget.TabsWidget


class MainWindow(QMainWindow):
    """Custom Main Window."""

    def __init__(self):
        super().__init__()
        logger.info('Stash of Exile %s starting', consts.VERSION)
        self.resize(1280, 720)
        self.setWindowTitle(f'Stash of Exile {consts.VERSION}')

        QFontDatabase.addApplicationFont(TTF_FILE)

        # QSS file
        with open(QSS_FILE, 'r', encoding='utf-8') as f:
            self.setStyleSheet(f.read())

        # Status bar
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)
        widget = QWidget()
        layout = QHBoxLayout(widget)
        button = QPushButton('Error Log')
        button.clicked.connect(
            lambda: self.log_widget.setVisible(not self.log_widget.isVisible())
        )
        layout.setContentsMargins(0, 0, 5, 5)
        layout.addWidget(button, 0, Qt.AlignmentFlag.AlignRight)
        status_bar.addWidget(widget, 1)

        # Screen widgets
        self.center_widget = QWidget(self)
        self.setCentralWidget(self.center_widget)
        self.central_layout = QVBoxLayout(self.center_widget)

        # Start API thread
        self.api_thread = api.APIThread()
        self.api_thread.output.connect(MainWindow.callback)
        self.api_thread.status_output.connect(self.update_status)

        # Start download thread
        self.download_thread = download.DownloadThread()

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

        # Init logging widget
        self.log_widget = log.qlogger.create_widget()
        self.log_widget.setMinimumHeight(300)
        self.log_widget.setMaximumHeight(300)
        self.central_layout.addWidget(self.log_widget)
        self.log_widget.setVisible(False)

        # Default to login widget on start
        self.switch_widget(self.login_widget)

    def closeEvent(  # pylint: disable=invalid-name
        self, _: QCloseEvent
    ) -> None:
        """Exits the application."""
        logger.info('Stash of Exile exiting')
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
