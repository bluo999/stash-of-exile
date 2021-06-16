from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow: QtWidgets.QMainWindow):
        MainWindow.setObjectName('MainWindow')
        MainWindow.resize(1280, 720)
        with open('styles.qss', 'r') as f:
            MainWindow.setStyleSheet(f.read())

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox)
        self.formLayout = QtWidgets.QFormLayout()
        self.label = QtWidgets.QLabel(self.groupBox)
        self.formLayout.setWidget(
            2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label
        )
        self.filterCategory = QtWidgets.QComboBox(self.groupBox)
        self.formLayout.setWidget(
            2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.filterCategory
        )
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.formLayout.setWidget(
            4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_2
        )
        self.group = QtWidgets.QHBoxLayout()
        self.lineEdit_5 = QtWidgets.QLineEdit(self.groupBox)
        self.group.addWidget(self.lineEdit_5)
        self.lineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.group.addWidget(self.lineEdit)
        self.formLayout.setLayout(
            4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.group
        )
        self.filterRarity = QtWidgets.QComboBox(self.groupBox)
        self.formLayout.setWidget(
            3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.filterRarity
        )
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.formLayout.setWidget(
            3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_4
        )
        self.filterName = QtWidgets.QLineEdit(self.groupBox)
        self.formLayout.setWidget(
            0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.filterName
        )
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.formLayout.setWidget(
            0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_3
        )
        self.verticalLayout_2.addLayout(self.formLayout)
        self.verticalLayout.addWidget(self.groupBox)

        self.tooltip = QtWidgets.QTextEdit(self.centralwidget)
        self.tooltip.setReadOnly(True)
        self.verticalLayout.addWidget(self.tooltip)
        self.tooltipImage = QtWidgets.QTextEdit(self.centralwidget)
        self.tooltipImage.setReadOnly(True)
        self.verticalLayout.addWidget(self.tooltipImage)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.tableView = QtWidgets.QTableView(self.centralwidget)
        self.tableView.setMinimumSize(QtCore.QSize(200, 0))
        self.tableView.setMouseTracking(True)
        self.tableView.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.AdjustToContents
        )
        self.tableView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableView.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.tableView.setHorizontalScrollMode(
            QtWidgets.QAbstractItemView.ScrollPerPixel
        )
        self.tableView.setShowGrid(False)
        self.tableView.setSortingEnabled(True)
        self.tableView.setWordWrap(False)

        self.horizontalLayout.addWidget(self.tableView)
        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1280, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate('MainWindow', 'Stash Of Exile'))
        self.groupBox.setTitle(_translate('MainWindow', 'Filters'))
        self.label.setText(_translate('MainWindow', 'Category:'))
        self.label_2.setText(_translate('MainWindow', 'Item Level:'))
        self.label_4.setText(_translate('MainWindow', 'Rarity:'))
        self.label_3.setText(_translate('MainWindow', 'Name:'))
