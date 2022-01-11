"""
Entrypoint of Stash of Exile.
"""

import sys

from PyQt6.QtWidgets import QApplication

import mainwindow

if __name__ == '__main__':
    print(__file__)
    app = QApplication(sys.argv)

    main_window = mainwindow.MainWindow()
    sys.exit(app.exec())
