# api/openai_api.py
import json
import re
from openai import OpenAI
from utils.config import DEFAULT_VISION_MODEL, CLASSIFY_PROMPT, DEFAULT_DEFECT_LABELS
from utils.file_handler import to_data_url

client = OpenAI()

DEFECT_LABELS = [lbl.strip() for lbl in DEFAULT_DEFECT_LABELS.split(",") if lbl.strip()]

def _extract_json(text: str) -> str:
    """응답 중 첫 번째 JSON 오브젝트만 추출"""
    codeblock = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S | re.I)
    if codeblock:
        return codeblock.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text  # fallback

def _normalize_label(lbl: str) -> str:
    """라벨 소문자/공백 정리 후 DEFECT_LABELS에 맞게 보정"""
    if not lbl:
        return DEFECT_LABELS[0] if DEFECT_LABELS else "none"
    norm = lbl.strip().lower().replace(" ", "_")
    allowed = {l.strip().lower().replace(" ", "_"): l.strip() for l in DEFECT_LABELS}
    return allowed.get(norm, DEFECT_LABELS[0] if DEFECT_LABELS else "none")

def _clamp_confidence(x) -> float:
    try:
        v = float(x)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, v))

def classify_image(image_path: str) -> dict:
    """
    반환:
    {
        "label": "dent",
        "confidence": 0.92,
        "description": "...",
        "severity": "A",
        "location": "front bumper",
        "action": "Rework"
    }
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
        raw = resp.choices[0].message.content or ""
        js = _extract_json(raw)
        parsed = json.loads(js)

        label = _normalize_label(parsed.get("label", ""))
        confidence = _clamp_confidence(parsed.get("confidence", 0.0))
        description = str(parsed.get("description", "")).strip() or "(설명 없음)"
        severity = str(parsed.get("severity", "C"))
        location = str(parsed.get("location", "unknown")).strip()
        action = str(parsed.get("action", "Hold"))

        return {
            "label": label,
            "confidence": confidence,
            "description": description,
            "severity": severity,
            "location": location,
            "action": action,
        }

    except Exception as e:
        return {
            "label": DEFECT_LABELS[0] if DEFECT_LABELS else "none",
            "confidence": 0.0,
            "description": f"[오류] {e}",
            "severity": "C",
            "location": "unknown",
            "action": "Hold",
        }