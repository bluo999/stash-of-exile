import sys

from dataclasses import dataclass
from PyQt6.QtCore import QAbstractTableModel, QSortFilterProxyModel, Qt

from PyQt6.QtWidgets import QApplication, QListView, QMainWindow, QTableView


@dataclass
class Item:
    name: str
    id: int


class StatusFilterModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        QSortFilterProxyModel.__init__(self, parent)
        self._id = None

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        self._id = id
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent) -> bool:
        if self.id is None:
            return True
        source_index = self.sourceModel().index(source_row, 0, source_parent)
        id = source_index.data()
        print(id, self.id)
        return self.id == id


class TestModel(QAbstractTableModel):
    def __init__(self, items, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._items = items

    def headerData(self, section, orientation, role):
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return 'Name'

    def columnCount(self, parent):
        return 1

    def rowCount(self, parent):
        return len(self._items)

    def data(self, index, role):
        column = index.column()
        item = self._items[index.row()]
        if column == 0:
            if role == Qt.ItemDataRole.DisplayRole:
                return item.name


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_window = QMainWindow()

    items = [Item('a', 1), Item('b', 5), Item('c', 2)]

    model = TestModel(items)

    table = QTableView()
    table.show()
    table.setModel(model)

    list = QListView()
    list.show()
    proxy = StatusFilterModel()
    proxy.setSourceModel(model)
    proxy.id = 5
    list.setModel(proxy)

    sys.exit(app.exec())
