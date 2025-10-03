import os
import random
import shutil
from pathlib import Path

# ==========================================
# 🔧 사용자 수정 영역
SRC_ROOT = r"C:\ROKEY\SETUP\CARDD_RELEASE\CarDD_COCO"   # 원본 COCO 데이터셋 폴더 (train/test/val 포함)
DST_ROOT = r"C:\ROKEY\SETUP\CarDD_SAMPLES"              # 결과 저장 폴더
NUM_SAMPLES = 10                                       # 뽑을 총 이미지 수
SEED = 42                                               # 랜덤 시드
EXTS = (".jpg", ".jpeg", ".png")                        # 포함할 이미지 확장자
# ==========================================


def clear_folder(folder: Path):
    """폴더 내부 비우기 (폴더 자체는 유지)"""
    if folder.exists():
        for item in folder.iterdir():
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)


def sample_and_copy_images(src_root, dst_root, num_samples, seed=42, exts=(".jpg", ".jpeg", ".png")):
    """
    CarDD_COCO 하위 모든 폴더(train2017, val2017, test2017 등)에서
    num_samples 개수를 랜덤 선택해 dst_root에 복사
    """
    random.seed(seed)
    src_root = Path(src_root)
    dst_root = Path(dst_root)
    dst_root.mkdir(parents=True, exist_ok=True)

    # 실행 시마다 폴더 비우기
    clear_folder(dst_root)

    # 모든 이미지 파일 모으기 (재귀적으로)
    all_images = [f for f in src_root.rglob("*") if f.suffix.lower() in exts]

    if not all_images:
        print(f"[WARN] {src_root} 에 이미지가 없습니다.")
        return

    n = min(num_samples, len(all_images))
    chosen = random.sample(all_images, n)

    print(f"총 {len(all_images)}개 중 {n}개 복사 중...")

    for f in chosen:
        shutil.copy2(f, dst_root / f.name)

    print(f"완료 (결과 폴더: {dst_root.resolve()})")


if __name__ == "__main__":
    sample_and_copy_images(SRC_ROOT, DST_ROOT, NUM_SAMPLES, SEED, EXTS)