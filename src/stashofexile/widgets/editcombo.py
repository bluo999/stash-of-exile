"""
Defines an EditComboBox.
"""

from typing import Optional

from PyQt6 import QtGui
from PyQt6.QtCore import QAbstractItemModel, Qt
from PyQt6.QtWidgets import (QComboBox, QCompleter, QLineEdit, QListView,
                             QWidget)


class ClickLineEdit(QLineEdit):
    """Line edit that pops up a completer on click."""

    def __init__(self, completer: QCompleter, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._completer = completer

    def mousePressEvent(  # pylint: disable=invalid-name
        self, e: QtGui.QMouseEvent
    ) -> None:
        """Open completer on click."""
        super().mousePressEvent(e)
        if e.button() == Qt.MouseButton.LeftButton:
            if not self._completer.popup().isVisible():
                self._completer.complete()


class ECBox(QComboBox):
    """QComboBox with a line edit to filter through the options."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        view = self.view()
        assert isinstance(view, QListView)
        view.setUniformItemSizes(True)

        completer = QCompleter(self.model(), self)
        view = completer.popup()
        assert isinstance(view, QListView)
        view.setUniformItemSizes(True)

        # Cusutom LineEdit
        self.setLineEdit(ClickLineEdit(completer))
        self.lineEdit().textChanged.connect(self.text_changed)

        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setModelSorting(QCompleter.ModelSorting.CaseInsensitivelySortedModel)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setMaxVisibleItems(10)
        completer.activated.connect(self.on_completer_activated)
        self.setCompleter(completer)

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
        """Also update completer model."""
        super().setModel(model)
        self.completer().setModel(model)

    def setModelColumn(self, visibleColumn: int):  # pylint: disable=invalid-name
        """Also update completer column."""
        super().setModelColumn(visibleColumn)
        self.completer().setCompletionColumn(visibleColumn)

    def focusOutEvent(  # pylint: disable=invalid-name
        self, e: QtGui.QFocusEvent
    ) -> None:
        """Resets LineEdit text and completion prefix to selected text."""
        text = self.itemText(self.currentIndex())
        self.setEditText(text)
        self.completer().setCompletionPrefix(text)
        super().focusOutEvent(e)


class BoolECBox(ECBox):
    """EditComboBox with blank, yes, and no."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.addItems(('Yes', 'No'))
