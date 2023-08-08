"""
Handles tooltip display of items.
"""

import os
from typing import TYPE_CHECKING

from PyQt6.QtCore import QItemSelection, Qt
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (QApplication, QFrame, QLabel, QPushButton,
                             QTextEdit, QVBoxLayout, QWidget)

from stashofexile import consts

if TYPE_CHECKING:
    from stashofexile.widgets import mainwidget

SEPARATOR_DIR = os.path.join(consts.ASSETS_DIR, 'separator')


class TooltipWidget(QWidget):
    """Widget for the item tooltip display."""

    def __init__(self, main_widget: 'mainwidget.MainWidget') -> None:
        super().__init__()
        self.main = main_widget
        self._static_build()

    def _static_build(self) -> None:
        middle_vlayout = QVBoxLayout(self)
        middle_vlayout.setSpacing(0)

        # Image
        self.image = QLabel()
        self.image.setFrameStyle(QFrame.Shape.NoFrame)
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image.setObjectName('Image')
        middle_vlayout.addWidget(self.image)

        # Tooltip
        self.tooltip = QTextEdit()
        self.tooltip.setFrameStyle(QFrame.Shape.NoFrame)
        self.tooltip.setReadOnly(True)
        self.tooltip.setFont(QFont('Fontin SmallCaps', 12))
        self.tooltip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tooltip.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tooltip.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        middle_vlayout.addWidget(self.tooltip)

        copy_button = QPushButton()
        copy_button.setText('Copy Item Text')
        middle_vlayout.addWidget(copy_button)
        copy_button.clicked.connect(self._copy_item_text)

    def _copy_item_text(self) -> None:
        """Copies item text to clipboard."""
        if not self.main.table:
            return

        if not self.main.table.selectedIndexes():
            return

        row = self.main.table.selectedIndexes()[0].row()
        item = self.main.model.current_items[row]
        QApplication.clipboard().setText(item.get_text())

    def update_tooltip(self, selected: QItemSelection) -> None:
        """Updates tooltip image and description."""
        if not selected.indexes():
            # Nothing selected
            return

        row = selected.indexes()[0].row()
        item = self.main.model.current_items[row]

        # Update image
        self.image.setPixmap(item.get_image())

        # Update tooltip
        self.tooltip.setHtml('')
        sections = item.get_tooltip()
        width = self.tooltip.width() - self.tooltip.verticalScrollBar().width()

        # Construct tooltip from sections
        separator = os.path.join(
            SEPARATOR_DIR,
            consts.FRAME_TYPES.get(item.rarity, consts.FRAME_TYPES['normal']),
        )
        for i, html in enumerate(sections):
            self.tooltip.append(html)
            self.tooltip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if i != len(sections) - 1:
                self.tooltip.append(consts.SEPARATOR_TEMPLATE.format(separator, width))

        # Reset scroll to top
        self.tooltip.moveCursor(QTextCursor.MoveOperation.Start)
