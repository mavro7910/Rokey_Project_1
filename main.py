import sys
from PyQt5 import QtWidgets
from gui.main_window import Ui_MainWindow

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 버튼 클릭 이벤트 연결 예시
        self.btnUpload.clicked.connect(self.upload_image)
        self.btnView.clicked.connect(self.view_results)

    def upload_image(self):
        print("Upload Image clicked!")

    def view_results(self):
        print("View Results clicked!")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())