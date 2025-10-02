from PyQt5 import QtWidgets, QtGui, QtCore
from gui.main_window import Ui_MainWindow

from utils.file_handler import get_image_file
from api.openai_api import classify_image
from db.db import insert_note, fetch_notes

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.current_image_path = None
        self.ui.tableResults.cellDoubleClicked.connect(self._on_row_dbl_clicked)

        # 버튼 이벤트 연결
        self.ui.btnUpload.clicked.connect(self.on_upload_image)
        self.ui.btnClassify.clicked.connect(self.on_classify)
        self.ui.btnSave.clicked.connect(self.on_save)
        self.ui.btnView.clicked.connect(self.on_view_results)

        # 테이블 기본 설정
        t = self.ui.tableResults
        t.setSelectionBehavior(t.SelectRows)
        t.setEditTriggers(t.NoEditTriggers)
        t.horizontalHeader().setStretchLastSection(True)

    # ---------- 이벤트 ----------
    def on_upload_image(self):
        path = get_image_file()
        if not path:
            return
        self.current_image_path = path
        self._set_preview(path)

    def on_classify(self):
        if not self.current_image_path:
            QtWidgets.QMessageBox.information(self, "안내", "먼저 이미지를 업로드하세요.")
            return
        self.ui.txtResult.setPlainText("불량 유형 분류 중…")
        result = classify_image(self.current_image_path)   # {'label','confidence','description'}
        # 우측 패널엔 설명을 보여주고
        self.ui.txtResult.setPlainText(result["description"])
        # 저장은 Save 버튼을 따로 누를 때 함께 저장되도록(또는 즉시 저장 원하면 여기서 insert_note 호출)
        self._last_classify = result   # 임시 보관

    def on_save(self):
        if not self.current_image_path:
            QtWidgets.QMessageBox.information(self, "안내", "이미지를 먼저 업로드하세요.")
            return
        desc = self.ui.txtResult.toPlainText().strip()
        if not desc:
            QtWidgets.QMessageBox.information(self, "안내", "저장할 설명이 없습니다.")
            return

        label = None
        confidence = None
        if hasattr(self, "_last_classify"):
            label = self._last_classify.get("label")
            confidence = self._last_classify.get("confidence")

        insert_note(self.current_image_path, desc, label, confidence)
        QtWidgets.QMessageBox.information(self, "완료", "DB에 저장했습니다.")
        self.on_view_results()

    def on_view_results(self):
        rows = fetch_notes(limit=200)  # (id, image_path, label, confidence, description, created_at)
        t = self.ui.tableResults
        t.setRowCount(0)
        for rid, fpath, label, conf, desc, created_at in rows:
            r = t.rowCount()
            t.insertRow(r)
            t.setItem(r, 0, QtWidgets.QTableWidgetItem(str(rid)))             # ID
            t.setItem(r, 1, QtWidgets.QTableWidgetItem(fpath))                # File
            t.setItem(r, 2, QtWidgets.QTableWidgetItem(label or ""))          # Label
            # conf가 None이면 빈칸, 숫자면 소수점 2자리 포맷
            t.setItem(r, 3, QtWidgets.QTableWidgetItem("" if conf is None else f"{float(conf):.2f}"))
            t.setItem(r, 4, QtWidgets.QTableWidgetItem(desc or ""))           # Description
            t.setItem(r, 5, QtWidgets.QTableWidgetItem(created_at or ""))     # Data(=created_at)


    # ---------- 보조 ----------
    def _set_preview(self, path: str):
        pix = QtGui.QPixmap(path)
        if pix.isNull():
            QtWidgets.QMessageBox.warning(self, "오류", "이미지를 불러오지 못했습니다.")
            return
        # lblImage.setScaledContents(True) 설정되어 있으므로 자동 스케일
        self.ui.lblImage.setPixmap(pix)
        self.ui.lblImage.setToolTip(path)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_image_path and self.ui.lblImage.pixmap():
            self.ui.lblImage.setPixmap(QtGui.QPixmap(self.current_image_path))

    def _on_row_dbl_clicked(self, row, col):
        fpath = self.ui.tableResults.item(row, 1).text()
        desc  = self.ui.tableResults.item(row, 4).text()
        self.ui.txtResult.setPlainText(desc)
        if QtCore.QFileInfo(fpath).exists():
            self.current_image_path = fpath
            self._set_preview(fpath)
        else:
            QtWidgets.QMessageBox.warning(self, "경고", "로컬에 이미지 파일이 없습니다.")
