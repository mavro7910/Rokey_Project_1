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

# 라벨을 리스트로 사용 가능하도록 변환
DEFECT_LABELS = [lbl.strip() for lbl in DEFAULT_DEFECT_LABELS.split(",") if lbl.strip()]

CLASSIFY_PROMPT = os.getenv(
    "CLASSIFY_PROMPT",
    f"""
다음 자동차 이미지를 분석하여 JSON으로만 결과를 출력하라.

필드 요구사항:
- label: 아래 라벨 목록 중 하나 (단일 값)
  라벨 목록: {DEFAULT_DEFECT_LABELS}
- confidence: 0~1 사이 숫자
- description: 한국어로 간단 설명
- severity: A/B/C 중 하나 (A=치명적, B=중대, C=경미)
- location: 결함이 발생한 자동차 부위 (예: front bumper, rear bumper, hood, trunk, left door, right door, roof, windshield 등)
- action: Pass / Rework / Scrap / Hold / Reject 중 하나

반드시 아래 JSON 형식으로만 출력하라(추가 텍스트 금지):
{{
  "label":"<라벨>",
  "confidence":<0~1 숫자>,
  "description":"<한국어 설명>",
  "severity":"<A|B|C>",
  "location":"<부위 텍스트>",
  "action":"<Pass|Rework|Scrap|Hold|Reject>"
}}
"""
)

SEVERITY_UI = ["High", "Medium", "Low"]
SEVERITY_MAP = {
    "High": "A",
    "Medium": "B",
    "Low": "C"
}
SEVERITY_MAP_REVERSE = {v: k for k, v in SEVERITY_MAP.items()}