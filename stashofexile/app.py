"""
Entrypoint of Stash of Exile.
"""

import sys

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QColor, QColorConstants, QPalette
from PyQt6.QtWidgets import QApplication

from stashofexile import mainwindow


def main() -> None:
    """Entrypoint function."""
    # Dark colors
    QApplication.setStyle("fusion")
    dark = QPalette()
    dark.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark.setColor(QPalette.ColorRole.WindowText, QColorConstants.White)
    dark.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    dark.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
    dark.setColor(QPalette.ColorRole.ToolTipText, QColorConstants.White)
    dark.setColor(QPalette.ColorRole.Text, QColorConstants.White)
    dark.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark.setColor(QPalette.ColorRole.ButtonText, QColorConstants.White)
    dark.setColor(QPalette.ColorRole.BrightText, QColorConstants.Red)
    dark.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark.setColor(QPalette.ColorRole.HighlightedText, QColor(35, 35, 35))
    dark.setColor(QPalette.ColorRole.PlaceholderText, QColorConstants.LightGray)
    dark.setColor(
        QPalette.ColorGroup.Active, QPalette.ColorRole.Button, QColor(53, 53, 53)
    )
    dark.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColorConstants.DarkGray,
    )
    dark.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        QColorConstants.DarkGray,
    )
    dark.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColorConstants.DarkGray
    )
    dark.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.Light, QColor(53, 53, 53)
    )
    QApplication.setPalette(dark)

    app = QApplication(sys.argv)
    window = mainwindow.MainWindow()
    window.show()
    sys.exit(app.exec())
