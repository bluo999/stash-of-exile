import os

from typing import List
from PyQt6.QtCore import QRect
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QMenuBar, QStatusBar, QWidget

from loginwidget import LoginWidget
from mainwidget import MainWidget
from tabswidget import TabsWidget

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


class MainWindow(QMainWindow):
    """Custom Main Window."""

    def __init__(self):
        QMainWindow.__init__(self)
        self.resize(1280, 720)
        self.setWindowTitle('Stash of Exile')

        # A font by Jos Buivenga (exljbris) -> www.exljbris.com
        QFontDatabase.addApplicationFont('../assets/FontinSmallCaps.ttf')

        # QSS file
        with open(os.path.join(__location__, 'styles.qss'), 'r') as f:
            self.setStyleSheet(f.read())

        # Menu bar
        menuBar = QMenuBar(self)
        menuBar.setGeometry(QRect(0, 0, 1280, 21))
        self.setMenuBar(menuBar)

        # Status bar
        statusBar = QStatusBar(self)
        self.setStatusBar(statusBar)

        # Screen widgets
        self.centerWidget = QWidget(self)
        self.setCentralWidget(self.centerWidget)
        self.centralLayout = QHBoxLayout(self.centerWidget)

        self.loginWidget = LoginWidget(self)
        self.tabsWidget = TabsWidget(self)
        self.mainWidget = MainWidget(self)
        self.widgets: List[QWidget] = [
            self.loginWidget,
            self.tabsWidget,
            self.mainWidget,
        ]
        for widget in self.widgets:
            self.centralLayout.addWidget(widget)

        self.switchWidget(self.loginWidget)

        # Show window
        self.show()

    def switchWidget(self, destWidget: QWidget, *args):
        assert destWidget in self.widgets
        for widget in self.widgets:
            if widget == destWidget:
                widget.setEnabled(True)
                widget.show()
            else:
                widget.setDisabled(True)
                widget.hide()

        destWidget.onShow(*args)
