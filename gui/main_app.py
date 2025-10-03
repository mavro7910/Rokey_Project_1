from PyQt5 import QtWidgets, QtGui, QtCore
from gui.main_window import Ui_MainWindow

from utils.file_handler import get_image_file
from api.openai_api import classify_image
from db.db import insert_note, fetch_notes

# 추가: 표준 라이브러리
from pathlib import Path

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 현재 단일 파일 상태
        self.current_image_path = None

        # 추가: 폴더 업로드용 배치 상태
        self._batch_files = []   # 선택한 폴더 내 이미지 전체 경로 리스트(str)
        self._batch_idx = -1     # 현재 인덱스

        self.ui.tableResults.cellDoubleClicked.connect(self._on_row_dbl_clicked)

        # 버튼 이벤트 연결
        self.ui.btnUpload.clicked.connect(self.on_upload_image)   # 단일 파일
        self.ui.pushButton.clicked.connect(self.on_upload_folder) # 폴더 선택
        self.ui.btnClassify.clicked.connect(self.on_classify)
        self.ui.btnSave.clicked.connect(self.on_save)
        self.ui.btnView.clicked.connect(self.on_view_results)

        # 테이블 기본 설정
        t = self.ui.tableResults
        t.setSelectionBehavior(t.SelectRows)
        t.setEditTriggers(t.NoEditTriggers)
        t.horizontalHeader().setStretchLastSection(True)

        # === 추가: 툴바 & "Upload Folder…" 액션 (UI 수정 없이 폴더 업로드 제공) ===
        self._ensure_toolbar_for_folder_upload()

    # ---------- 이벤트 ----------
    def on_upload_image(self):
        """기존: 단일 파일 업로드"""
        path = get_image_file()
        if not path:
            return
        self._batch_files = []      # 단일 파일 모드로 전환
        self._batch_idx = -1
        self.current_image_path = path
        self._set_preview(path)
        self.ui.txtResult.clear()

    def on_classify(self):
        if not self.current_image_path:
            QtWidgets.QMessageBox.information(self, "안내", "먼저 이미지를 업로드하세요.")
            return
        self.ui.txtResult.setPlainText("불량 유형 분류 중…")
        result = classify_image(self.current_image_path)   # {'label','confidence','description'}
        # 우측 패널엔 설명을 보여주고
        self.ui.txtResult.setPlainText(result["description"])
        # 저장은 Save 버튼을 따로 누를 때 함께 저장되도록
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

        try:
            insert_note(self.current_image_path, desc, label, confidence)
            QtWidgets.QMessageBox.information(self, "완료", "DB에 저장했습니다.")
        except Exception as e:
            print("[ERROR][on_save]", e)  # 콘솔 로그
            QtWidgets.QMessageBox.critical(self, "DB 오류", f"저장 중 오류 발생: {e}")
            return

        self.on_view_results()
        self._advance_batch_if_any()

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
            t.setItem(r, 5, QtWidgets.QTableWidgetItem(created_at or ""))     # Date(=created_at)

    # ---------- 폴더 업로드 핵심 ----------
    def on_upload_folder(self):
        """폴더 선택 → 하위 이미지 전체를 GPT로 판정 → 각각 DB에 저장 (일괄처리)"""
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select image folder")
        if not folder:
            return

        base = Path(folder)
        # 이미지 후보 수집
        candidates = [
            str(p) for p in base.rglob("*")
            if p.is_file() and self._is_image_file(p)
        ]
        if not candidates:
            QtWidgets.QMessageBox.information(self, "No images", "선택한 폴더에 이미지가 없습니다.")
            return

        # (선택) 이미 DB에 있는 경로는 스킵하고 싶다면 기존 경로 set을 만든다
        try:
            existing_rows = fetch_notes(limit=100000)   # 충분히 크게
            existing_paths = {row[1] for row in existing_rows}  # (id, image_path, label, confidence, desc, created_at)
        except Exception:
            existing_paths = set()

        # 중복 제거(동일 경로) + DB에 이미 있는 항목 스킵
        unique_paths = []
        seen = set()
        for f in candidates:
            if f in seen:
                continue
            seen.add(f)
            if f in existing_paths:
                continue
            unique_paths.append(f)

        if not unique_paths:
            QtWidgets.QMessageBox.information(self, "안내", "새로 저장할 이미지가 없습니다.")
            return

        # 진행률 다이얼로그
        prog = QtWidgets.QProgressDialog("폴더 일괄 판정/저장 중…", "취소", 0, len(unique_paths), self)
        prog.setWindowModality(QtCore.Qt.WindowModal)
        prog.setMinimumDuration(300)

        saved = 0
        errors = 0

        for i, fpath in enumerate(unique_paths, start=1):
            if prog.wasCanceled():
                break
            try:
                # 미리보기는 진행 상태 확인용 (원치 않으면 주석)
                self.current_image_path = fpath
                self._set_preview(fpath)

                # 1) GPT 판정
                result = classify_image(fpath)     # {'label','confidence','description'}
                label = result.get("label")
                conf  = result.get("confidence")
                desc  = result.get("description") or ""

                # 2) DB 저장
                insert_note(fpath, desc, label, conf)
                saved += 1

                # 우측 패널 텍스트 갱신(옵션)
                self.ui.txtResult.setPlainText(desc)

            except Exception as e:
                print("[BATCH ERROR]", fpath, e)
                errors += 1

            prog.setValue(i)
            QtWidgets.QApplication.processEvents()

        prog.close()
        self.on_view_results()

        QtWidgets.QMessageBox.information(
            self, "완료",
            f"총 {len(unique_paths)}개 중 {saved}개 저장"
            + (f", 오류 {errors}개" if errors else "")
            + (", 취소됨" if saved + errors < len(unique_paths) else "")
        )


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
            self._batch_files = []   # DB에서 선택하면 배치 모드 해제
            self._batch_idx = -1
            self.current_image_path = fpath
            self._set_preview(fpath)
        else:
            QtWidgets.QMessageBox.warning(self, "경고", "로컬에 이미지 파일이 없습니다.")

    # === 추가: 도우미들 ===
    def _ensure_toolbar_for_folder_upload(self):
        """UI 파일을 안 고치고도 'Upload Folder…' 액션을 제공"""
        # 이미 툴바가 있다면 그대로 사용, 없으면 생성
        if not self.findChildren(QtWidgets.QToolBar):
            tb = QtWidgets.QToolBar("Main", self)
            self.addToolBar(tb)
        else:
            tb = self.findChildren(QtWidgets.QToolBar)[0]

        act = QtWidgets.QAction("Upload Folder…", self)
        act.setShortcut("Ctrl+Shift+U")
        act.triggered.connect(self.on_upload_folder)
        tb.addAction(act)

    def _is_image_file(self, path: Path) -> bool:
        return path.suffix.lower() in {
            ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tif", ".tiff"
        }

    def _advance_batch_if_any(self):
        """배치 모드에서 저장 후 다음 파일로 이동"""
        if not self._batch_files:
            return
        # 다음 인덱스
        self._batch_idx += 1
        if self._batch_idx >= len(self._batch_files):
            # 끝났으면 배치 모드 종료
            QtWidgets.QMessageBox.information(self, "배치 완료", "폴더 내 이미지 처리를 모두 마쳤습니다.")
            self._batch_files = []
            self._batch_idx = -1
            return
        # 다음 파일로 전환
        self.current_image_path = self._batch_files[self._batch_idx]
        self._set_preview(self.current_image_path)
        self.ui.txtResult.clear()
        # 직전 분류 결과 캐시 초기화
        if hasattr(self, "_last_classify"):
            delattr(self, "_last_classify")
