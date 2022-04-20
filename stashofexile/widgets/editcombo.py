"""
Defines an EditComboBox.
"""

from typing import Optional
from PyQt6 import QtGui
from PyQt6.QtCore import QAbstractItemModel, QSortFilterProxyModel, Qt
from PyQt6.QtWidgets import QComboBox, QCompleter, QLineEdit, QWidget


class ClickLineEdit(QLineEdit):
    """Line edit that pops up a completer on click."""

    def __init__(self, completer: QCompleter, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.test = completer

    def mousePressEvent(
        self, e: QtGui.QMouseEvent
    ) -> None:  # pylint: disable=invalid-name
        super().mousePressEvent(e)

        if e.button() == Qt.MouseButton.LeftButton:
            self.test.complete()


class ECBox(QComboBox):
    """QComboBox with a line edit to filter through the options."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        # Filter Model
        self.filter_model = QSortFilterProxyModel(self)
        self.filter_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.filter_model.setSourceModel(self.model())

        # Completer
        completer = QCompleter(self.filter_model, self)
        completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        completer.activated.connect(self.on_completer_activated)
        self.setCompleter(completer)

        # self.setLineEdit(ClickLineEdit(completer))
        self.lineEdit().textChanged.connect(self.text_changed)
        self.lineEdit().textEdited.connect(self.filter_model.setFilterFixedString)

        self.addItems(('',))

    def text_changed(self, text: str) -> None:
        """Clears selection when text is set to empty."""
        if text == '':
            self.setCurrentIndex(0)

    def on_completer_activated(self, text: str):
        """Sets selection when completer is activated."""
        if text:
            index = self.findText(text)
            self.setCurrentIndex(index)

    def setModel(self, model: QAbstractItemModel):  # pylint: disable=invalid-name
        """Sets model."""
        super().setModel(model)
        self.filter_model.setSourceModel(model)
        self.completer().setModel(self.filter_model)

    def setModelColumn(self, visibleColumn: int):  # pylint: disable=invalid-name
        """Sets model column."""
        super().setModelColumn(visibleColumn)
        self.completer().setCompletionColumn(visibleColumn)
        self.filter_model.setFilterKeyColumn(visibleColumn)

class BoolECBox(ECBox):
    """EditComboBox with blank, yes, and no."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.addItems(('Yes', 'No'))
