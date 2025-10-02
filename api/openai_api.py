# api/openai_api.py (추가)
import json
from openai import OpenAI
from utils.config import DEFAULT_VISION_MODEL, CLASSIFY_PROMPT
from utils.file_handler import to_data_url

client = OpenAI()

def classify_image(image_path: str) -> dict:
    """
    이미지 불량 유형 분류 + 신뢰도 + 설명을 JSON(dict)으로 반환.
    실패 시 {'label':'none','confidence':0.0,'description':'[오류] ...'} 반환.
    """
    try:
        data_url = to_data_url(image_path)
        resp = client.chat.completions.create(
            model=DEFAULT_VISION_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": CLASSIFY_PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }],
            temperature=0.2,
        )
        text = resp.choices[0].message.content or ""
        # JSON만 오도록 프롬프트를 강제했지만, 혹시 몰라서 안전 파싱
        start = text.find("{"); end = text.rfind("}")
        parsed = json.loads(text[start:end+1])
        # 필수 키 보정
        return {
            "label": str(parsed.get("label", "none")),
            "confidence": float(parsed.get("confidence", 0.0)),
            "description": str(parsed.get("description", "")).strip() or "(설명 없음)",
        }
    except Exception as e:
        return {"label":"none","confidence":0.0,"description":f"[오류] {e}"}
