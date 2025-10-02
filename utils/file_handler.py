# utils/file_handler.py
from PyQt5.QtWidgets import QFileDialog
import base64
import os

def get_image_file():
    path, _ = QFileDialog.getOpenFileName(
        None, '이미지 선택', '', 'Images (*.png *.jpg *.jpeg *.webp)'
    )
    return path

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def guess_mime(image_path: str) -> str:
    ext = os.path.splitext(image_path)[1].lower()
    if ext in (".jpg", ".jpeg"): return "image/jpeg"
    if ext in (".png",):          return "image/png"
    if ext in (".webp",):         return "image/webp"
    return "application/octet-stream"

def to_data_url(image_path: str) -> str:
    from .file_handler import encode_image_to_base64, guess_mime
    b64 = encode_image_to_base64(image_path)
    return f"data:{guess_mime(image_path)};base64,{b64}"
