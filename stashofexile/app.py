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

    _ = mainwindow.MainWindow()
    sys.exit(app.exec())
