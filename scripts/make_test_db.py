"""
가짜 데이터셋 생성기
- config.py의 DB_PATH, DEFECT_LABELS, SEVERITY_MAP 설정값을 사용
- 최근 90일간의 임의 날짜와 결함 데이터를 무작위로 생성
"""

import sys, os
import random
import sqlite3
from datetime import datetime, timedelta

# --- 패키지 인식용 경로 추가 ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import DEFECT_LABELS, SEVERITY_MAP

# =============================
# ⚙️ DB 설정
# =============================
FAKE_DB_PATH = os.path.join(os.getcwd(), "fake_app.db")  # ← 실제 app.db와 분리
if os.path.exists(FAKE_DB_PATH):
    os.remove(FAKE_DB_PATH)

print(f"[INFO] Creating fake DB: {FAKE_DB_PATH}")

# =============================
# ⚙️ DB 스키마 생성
# =============================
conn = sqlite3.connect(FAKE_DB_PATH)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT,
    image_path TEXT,
    image_hash TEXT,
    defect_type TEXT,
    severity TEXT,
    location TEXT,
    score REAL,
    detail TEXT,
    action TEXT,
    ts TEXT DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# =============================
# ⚙️ 더미 데이터 생성
# =============================
defect_types = DEFECT_LABELS
severities = list(SEVERITY_MAP.values())  # ['A', 'B', 'C']
locations = ["front bumper", "rear bumper", "hood", "trunk", "door", "roof", "windshield"]
actions = ["Pass", "Rework", "Scrap", "Hold", "Reject"]

start_date = datetime.now() - timedelta(days=120)  # 4개월 전부터 데이터 생성
n_rows = 500

for i in range(n_rows):
    created_at = start_date + timedelta(days=random.randint(0, 120), hours=random.randint(0, 23))
    cur.execute("""
        INSERT INTO results (
            file_name, image_path, image_hash,
            defect_type, severity, location, score, detail, action, ts
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        f"car_{i:04d}.jpg",
        f"/fake/path/car_{i:04d}.jpg",
        f"hash_{i:04d}",
        random.choice(defect_types),
        random.choice(severities),
        random.choice(locations),
        round(random.uniform(0.6, 0.99), 3),
        "Auto-generated test record",
        random.choice(actions),
        created_at.strftime("%Y-%m-%d %H:%M:%S")
    ))

conn.commit()
conn.close()
print(f"[DONE] Inserted {n_rows} fake rows into {FAKE_DB_PATH}")