"""
Entrypoint of Stash of Exile.
"""

import sys

from PyQt6.QtWidgets import QApplication

from stashofexile import mainwindow

def main() -> None:
    print(__file__)
    app = QApplication(sys.argv)

    main_window = mainwindow.MainWindow()
    sys.exit(app.exec())
