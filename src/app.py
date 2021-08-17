"""
Entrypoint of Stash of Exile.
"""

import sys

from PyQt6.QtWidgets import QApplication

from mainwindow import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_window = MainWindow()
    sys.exit(app.exec())
