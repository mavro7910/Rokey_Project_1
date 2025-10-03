import os
import random
import shutil
import stat
import time
from pathlib import Path

# ==========================================
# 🔧 사용자 수정 영역
SRC_ROOT = r"C:\ROKEY\SETUP\CARDD_RELEASE\CarDD_COCO"   # 원본 COCO 데이터셋 폴더 (train/test/val 포함)
DST_ROOT = r"C:\ROKEY\SETUP\CarDD_SAMPLES"              # 결과 저장 폴더
NUM_SAMPLES = 10                                        # 뽑을 총 이미지 수
SEED = 41                                               # 랜덤 시드
EXTS = (".jpg", ".jpeg", ".png")                        # 포함할 이미지 확장자
# ==========================================

def _handle_remove_readonly(func, path, exc_info):
    """읽기 전용/권한 문제로 삭제 실패 시 권한 수정 후 재시도"""
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass
    func(path)

def _robust_rmtree(folder: Path, max_tries: int = 5, delay: float = 0.3):
    """
    윈도우 락/읽기전용 등으로 rmtree 실패하는 경우를 대비한 강건 삭제.
    - 읽기전용 해제 후 재시도
    - 잠깐 대기하며 최대 N번 재시도
    - 그래도 실패하면 폴더명을 .old-타임스탬프로 변경(세이프가드)
    """
    folder = Path(folder)
    if not folder.exists():
        return

    # 안전장치: SRC_ROOT를 지우는 실수 방지
    src = Path(SRC_ROOT).resolve()
    dst = folder.resolve()
    if src == dst or str(dst).startswith(str(src) + os.sep):
        raise RuntimeError(f"[ABORT] DST_ROOT가 SRC_ROOT와 같거나 내부입니다: {dst} (SRC={src})")

    for i in range(max_tries):
        try:
            shutil.rmtree(folder, onerror=_handle_remove_readonly)
            return
        except Exception as e:
            if i == max_tries - 1:
                # 마지막 시도도 실패 → 이름 바꿔 피하기
                try:
                    backup = folder.with_name(folder.name + f".old-{int(time.time())}")
                    folder.rename(backup)
                except Exception:
                    pass
                raise
            time.sleep(delay)

def reset_folder(folder: Path):
    """폴더 자체를 완전히 삭제 후 다시 생성 (강건 모드)"""
    folder = Path(folder)
    if folder.exists():
        _robust_rmtree(folder)
    folder.mkdir(parents=True, exist_ok=True)

def sample_and_copy_images(src_root, dst_root, num_samples, seed=42, exts=(".jpg", ".jpeg", ".png")):
    """
    CarDD_COCO 하위 모든 폴더(train2017, val2017, test2017 등)에서
    num_samples 개수를 랜덤 선택해 dst_root에 복사
    """
    # random.seed(seed) # 실행할 때마다 다른 결과 원하면 주석처리
    src_root = Path(src_root).resolve()
    dst_root = Path(dst_root).resolve()

    # 실행 시마다 폴더 삭제 후 다시 생성 (강건)
    reset_folder(dst_root)

    # 모든 이미지 파일 모으기 (재귀적으로)
    all_images = [f for f in src_root.rglob("*") if f.is_file() and f.suffix.lower() in exts]

    if not all_images:
        print(f"[WARN] {src_root} 에 이미지가 없습니다.")
        return

    n = min(num_samples, len(all_images))
    chosen = random.sample(all_images, n)

    print(f"총 {len(all_images)}개 중 {n}개 복사 중...")

    for f in chosen:
        # 파일이 잠겨있을 수 있으니 읽기전용 해제 한번 시도
        try:
            os.chmod(f, stat.S_IWRITE)
        except Exception:
            pass
        shutil.copy2(f, dst_root / f.name)

    print(f"완료 (결과 폴더: {dst_root})")

if __name__ == "__main__":
    sample_and_copy_images(SRC_ROOT, DST_ROOT, NUM_SAMPLES, SEED, EXTS)
