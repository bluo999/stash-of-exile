import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

from main import dynamicBuild
from mainwidget import Ui_MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    dynamicBuild(ui)
    MainWindow.show()
    sys.exit(app.exec_())
