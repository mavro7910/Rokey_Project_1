from PyQt5 import QtWidgets, QtGui, QtCore
from gui.main_window import Ui_MainWindow

from utils.file_handler import get_image_file
from api.openai_api import classify_image
from db.db import insert_note, fetch_notes, ensure_schema, search_notes, delete_notes, get_db_path
import sqlite3

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

        # 툴바 검색, 삭제
        self._ensure_toolbar_for_search_and_delete()

        # 마지막 검색 조건
        self._last_search = None  # {'label':..., 'keyword':..., 'date_from':..., 'date_to':...} or None

    try:
        ensure_schema()  # 파라미터 없이 호출
        print("[DB PATH]", get_db_path())
    except Exception as e:
        print("[DB] ensure_schema error:", e)


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
            print(f"[SAVE] path={self.current_image_path}, label={label}, conf={confidence}, desc_len={len(desc)}")
            # insert_note가 성공/중복을 리턴하지 않는다면 그대로 호출하고 except만 잡아도 ok
            res = insert_note(self.current_image_path, desc, label, confidence)
            # res가 None일 수도 있으니 메시지만 일단 성공으로 처리
            QtWidgets.QMessageBox.information(self, "완료", "DB에 저장 시도 완료.")
        except Exception as e:
            print("[ERROR][on_save]", e)
            QtWidgets.QMessageBox.critical(self, "DB 오류", f"저장 중 오류 발생: {e}")
            return

        self._refresh_results()
        self._advance_batch_if_any()



    def on_view_results(self):
        rows = fetch_notes(limit=200)
        self._last_search = None  # 전체 보기 모드
        self._render_rows(rows)


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
        prog = QtWidgets.QProgressDialog("폴더 내 일괄 판정/저장 중…", "취소", 0, len(unique_paths), self)
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

        QtWidgets.QMessageBox.information(
            self, "완료",
            f"총 {len(unique_paths)}개 중 {saved}개 저장"
            + (f", 오류 {errors}개" if errors else "")
            + (", 취소됨" if saved + errors < len(unique_paths) else "")
        )

        self._refresh_results()

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

    # 툴바 액션 하나로 간단한 폼 다이얼로그 띄워서 날짜/라벨/키워드 입력받고 테이블 갱신
    def _ensure_toolbar_for_search_and_delete(self):
        # 툴바 확보
        if not self.findChildren(QtWidgets.QToolBar):
            tb = QtWidgets.QToolBar("Main", self)
            self.addToolBar(tb)
        else:
            tb = self.findChildren(QtWidgets.QToolBar)[0]

        # 검색
        self.actSearch = QtWidgets.QAction("Search…", self)
        self.actSearch.setShortcut("Ctrl+F")
        self.actSearch.triggered.connect(self.on_search_dialog)
        tb.addAction(self.actSearch)
        self.addAction(self.actSearch)

        # 삭제
        self.actDelete = QtWidgets.QAction("Delete Selected", self)
        self.actDelete.setShortcut("Del")
        self.actDelete.triggered.connect(self.on_delete_selected)
        tb.addAction(self.actDelete)
        self.addAction(self.actDelete)

    # 검색 다이얼로그 & 실행
    def on_search_dialog(self):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Search")
        form = QtWidgets.QFormLayout(dlg)

        edtLabel = QtWidgets.QLineEdit(dlg)     # 라벨(정확 일치)
        edtKeyword = QtWidgets.QLineEdit(dlg)   # 키워드 (부분 일치)
        edtFrom = QtWidgets.QDateEdit(dlg); edtFrom.setCalendarPopup(True); edtFrom.setDisplayFormat("yyyy-MM-dd"); edtFrom.setDate(QtCore.QDate.currentDate().addMonths(-1))
        edtTo = QtWidgets.QDateEdit(dlg); edtTo.setCalendarPopup(True); edtTo.setDisplayFormat("yyyy-MM-dd"); edtTo.setDate(QtCore.QDate.currentDate())

        form.addRow("Label (exact):", edtLabel)
        form.addRow("Keyword:", edtKeyword)
        form.addRow("From (YYYY-MM-DD):", edtFrom)
        form.addRow("To (YYYY-MM-DD):", edtTo)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, parent=dlg)
        form.addRow(btns)

        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)

        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return

        label = edtLabel.text().strip() or None
        keyword = edtKeyword.text().strip() or None
        date_from = edtFrom.date().toString("yyyy-MM-dd")
        date_to = edtTo.date().toString("yyyy-MM-dd")

        try:
            rows = search_notes(label=label, keyword=keyword, date_from=date_from, date_to=date_to, limit=500)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "검색 오류", str(e))
            return

        # 테이블 반영 (fetch_notes와 동일 포맷)
        t = self.ui.tableResults
        t.setRowCount(0)
        for rid, fpath, lbl, conf, desc, created_at in rows:
            r = t.rowCount()
            t.insertRow(r)
            t.setItem(r, 0, QtWidgets.QTableWidgetItem(str(rid)))
            t.setItem(r, 1, QtWidgets.QTableWidgetItem(fpath))
            t.setItem(r, 2, QtWidgets.QTableWidgetItem(lbl or ""))
            t.setItem(r, 3, QtWidgets.QTableWidgetItem("" if conf is None else f"{float(conf):.2f}"))
            t.setItem(r, 4, QtWidgets.QTableWidgetItem(desc or ""))
            t.setItem(r, 5, QtWidgets.QTableWidgetItem(created_at or ""))

        self._last_search = {
            "label": label,
            "keyword": keyword,
            "date_from": date_from,
            "date_to": date_to,
        }
        self._render_rows(rows)

    
    # 현재 테이블에서 선택된 행들의 id를 모아서 삭제 → 테이블 갱신:
    def on_delete_selected(self):
        t = self.ui.tableResults
        sel = t.selectionModel().selectedRows()  # 행 단위 선택 가정
        if not sel:
            QtWidgets.QMessageBox.information(self, "안내", "삭제할 행을 선택하세요.")
            return

        ids = []
        for idx in sel:
            rid_item = t.item(idx.row(), 0)  # 0열(ID)
            if rid_item:
                try:
                    ids.append(int(rid_item.text()))
                except ValueError:
                    pass
        if not ids:
            QtWidgets.QMessageBox.information(self, "안내", "유효한 ID가 없습니다.")
            return

        reply = QtWidgets.QMessageBox.question(self, "삭제 확인", f"{len(ids)}개 항목을 삭제할까요?", 
                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply != QtWidgets.QMessageBox.Yes:
            return

        try:
            deleted = delete_notes(ids)
            QtWidgets.QMessageBox.information(self, "완료", f"삭제됨: {deleted}개")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "삭제 오류", str(e))
            return

        self._refresh_results()
        self.ui.tableResults.clearSelection()
        self.ui.tableResults.scrollToTop()
        QtWidgets.QApplication.processEvents()


    def _render_rows(self, rows):
        t = self.ui.tableResults
        t.setUpdatesEnabled(False)
        sorting = t.isSortingEnabled()
        t.setSortingEnabled(False)

        t.clearContents()
        t.setRowCount(0)
        for rid, fpath, lbl, conf, desc, created_at in rows:
            r = t.rowCount()
            t.insertRow(r)
            t.setItem(r, 0, QtWidgets.QTableWidgetItem(str(rid)))
            t.setItem(r, 1, QtWidgets.QTableWidgetItem(fpath))
            t.setItem(r, 2, QtWidgets.QTableWidgetItem(lbl or ""))
            t.setItem(r, 3, QtWidgets.QTableWidgetItem("" if conf is None else f"{float(conf):.2f}"))
            t.setItem(r, 4, QtWidgets.QTableWidgetItem(desc or ""))
            t.setItem(r, 5, QtWidgets.QTableWidgetItem(created_at or ""))

        t.setSortingEnabled(sorting)
        t.setUpdatesEnabled(True)
        t.viewport().update()
        QtWidgets.QApplication.processEvents()


    def _refresh_results(self):
        try:
            if self._last_search:
                ctx = self._last_search
                rows = search_notes(
                    label=ctx.get("label"),
                    keyword=ctx.get("keyword"),
                    date_from=ctx.get("date_from"),
                    date_to=ctx.get("date_to"),
                    limit=500
                )
            else:
                rows = fetch_notes(limit=200)
            self._render_rows(rows)
        except Exception as e:
            print("[REFRESH ERROR]", e)
