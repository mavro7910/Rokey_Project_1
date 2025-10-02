# utils/config.py
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY  # SDK가 환경변수로 읽도록 보장

DB_PATH = os.getenv("DB_PATH", "image_log.db")

# DB 폴더 자동 생성
_db_dir = os.path.dirname(os.path.abspath(DB_PATH))
if _db_dir and not os.path.exists(_db_dir):
    os.makedirs(_db_dir, exist_ok=True)

# 중앙 관리값(원하면 .env에서 덮어쓰기)
DEFAULT_VISION_MODEL = os.getenv("VISION_MODEL", "gpt-4o-mini")
DEFAULT_VISION_PROMPT = os.getenv(
    "VISION_PROMPT", "이 이미지를 간단히 설명해줘. 핵심 특징만 한국어로 요약."
)

DEFAULT_DEFECT_LABELS = os.getenv(
    "DEFECT_LABELS",
    "scratch, crack, dent, discoloration, contamination, misalignment, missing_part, burr, deformation, none"
)
CLASSIFY_PROMPT = os.getenv(
    "CLASSIFY_PROMPT",
    f"""
다음 이미지의 불량 유형을 아래 라벨 중 하나로 분류하고, 신뢰도(0~1)와 간단 설명을 한국어로 작성하라.
라벨 목록: {DEFAULT_DEFECT_LABELS}

반드시 아래 JSON 형식으로만 출력하라(추가 텍스트 금지):
{{"label":"<라벨>","confidence":<0~1 숫자>,"description":"<한국어 설명>"}}
"""
)