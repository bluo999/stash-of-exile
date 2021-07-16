from PyQt6.QtCore import QRect
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QMainWindow, QMenuBar, QStatusBar

from loginwidget import LoginWidget
from mainwidget import MainWidget


class MainWindow(QMainWindow):
    """Custom Main Window."""

    def __init__(self):
        QMainWindow.__init__(self)
        self.resize(1280, 720)
        self.setWindowTitle('Stash of Exile')

        # A font by Jos Buivenga (exljbris) -> www.exljbris.com
        QFontDatabase.addApplicationFont('../assets/FontinSmallCaps.ttf')

        # QSS file
        with open('styles.qss', 'r') as f:
            self.setStyleSheet(f.read())

        # Menu bar
        menuBar = QMenuBar(self)
        menuBar.setGeometry(QRect(0, 0, 1280, 21))
        self.setMenuBar(menuBar)

        # Status bar
        statusBar = QStatusBar(self)
        self.setStatusBar(statusBar)

        self.loginWidget = LoginWidget(self)
        self.setCentralWidget(self.loginWidget)

        self.show()

    def login(self):
        self.loginWidget.setDisabled(True)
        self.mainWidget = MainWidget(self)
        self.setCentralWidget(self.mainWidget)
