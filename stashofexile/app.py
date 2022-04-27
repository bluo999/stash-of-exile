"""
Entrypoint of Stash of Exile.
"""

import sys

from PyQt6.QtWidgets import QApplication

from stashofexile import mainwindow


def main() -> None:
    """Entrypoint function."""
    print(__file__)
    app = QApplication(sys.argv)
    window = mainwindow.MainWindow()
    window.show()
    sys.exit(app.exec())
