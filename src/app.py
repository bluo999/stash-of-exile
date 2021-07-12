import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

from main import Ui_MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.staticBuild(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
