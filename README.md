# 자동차 불량 분류 보조 시스템 (VisionQC)

## 📌 주제 및 선정배경
자동차 산업에서는 품질 관리(QA/QC)를 위해 불량 부품 이미지를 빠르게 분류하고 기록하는 것이 중요합니다.  
기존 AOI 장비는 비용이 높고, 모든 불량을 완벽히 구분하지 못하는 한계가 있습니다.  

이에 불량 이미지를 자동으로 분류·설명하고, 결과를 DB에 저장·검색할 수 있는 **자동차 품질 관리 보조 시스템(VisionQC)**을 구현하고자 합니다.

---

## 🎯 목표
- 카메라로 촬영한 자동차 부품 이미지를 GPT로 분석  
- **스크래치, 균열, 오염, 납땜 불량** 등 유형 분류 + 설명 제공  
- 결과를 SQLite DB에 저장하고 PyQt5 GUI를 통해 검색·조회  

---

## 🛠 현재 진행 상황 (2025-10-03 기준)
- [x] **단일 이미지 업로드** → GPT 분류 및 설명 출력 (2025-09-28 완료)
- [x] **폴더 업로드** → 일괄 분류 후 DB 저장 (2025-09-30 완료)
- [x] **DB 스키마 정리** (`notes` 테이블만 유지, `image_path`/`image_hash` UNIQUE) (2025-10-01 완료)
- [x] **검색 기능 추가** (라벨, 키워드, 날짜 범위 필터링) (2025-10-02 완료)
- [x] **삭제 기능 추가** (선택된 행 삭제 후 갱신) (2025-10-02 완료)
- [ ] 이미지 썸네일 미리보기 (UI 개선 예정)
- [ ] 불량 유형/Confidence 분포 통계 시각화
- [ ] CSV/Excel Export

---

## 🧩 사용 기술
- Python, PyQt5 (GUI)
- OpenAI API (gpt-4o-mini)
- SQLite3 (DB 관리)
- dotenv (.env 환경변수 관리)

---

## ⚙️ .env 설정
루트 디렉토리에 `.env` 파일 생성:  

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
DB_PATH=app.db
👉 DB_PATH는 생략 시 app.db 기본값을 사용합니다.
👉 API Key는 OpenAI 계정에서 발급받아야 합니다.
```

## 📂 데이터셋 출처

본 프로젝트에서는 **CarDD (Car Damage Dataset)** 를 활용하여 GPT-4o mini 기반 분류 실험을 진행합니다.

CarDD는 차량 외장 손상 이미지 약 4,000장을 포함하고 있으며, 스크래치, 찌그러짐, 페인트 손상 등 다양한 불량 유형을 포함합니다.

- [CarDD 공식 페이지](https://cardd-ustc.github.io/?utm_source=chatgpt.com)

## 전체 흐름

1. 이미지 업로드
2. 프롬프트(분류 요청) 전달
3. GPT-4o-mini를 통한 불량 유형 분류/설명
4. 결과 출력 및 SQLite DB 저장
5. 검색 기능으로 불량 유형/날짜별 탐색

## 🔧 시스템 구성도
```css
[ 사용자 ]
   ↓
[ PyQt5 GUI ]
   ↓                ↘
[ 이미지 업로드 + 프롬프트 ]   [ 검색 질의 ]
   ↓                          ↘
[ GPT-4o mini API 호출 ]      [ SQLite DB ]
   ↓                          ↗
[ 불량 유형 분류 + 설명 출력 ]
   ↓
[ 결과 DB 저장 및 화면 표시 ]
```

## 📁 디렉토리 구조
```css
defect_inspector/
├── gui/
│   └── main_app.py
│   └── main_window.py
├── api/
│   └── openai_api.py
├── db/
│   └── db.py
├── utils/
│   └── config.py
│   └── file_handler.py
├── main.py
├── app.db
├── .env.example
└── requirements.txt
```

## 📷 예시 시나리오

- 공정 중 부품 이미지를 촬영
- GPT가 자동으로 불량 유형 태깅 (예: “스크래치, confidence=0.82”)
- DB에 날짜·불량 유형 저장
- 검색어 “스크래치”, “9월 균열” 등으로 빠른 조회

## 🚀 확장 아이디어

- 결과를 CSV/Excel로 export
- 불량 유형/기간별 **통계 대시보드 (matplotlib 시각화)**
- GPT 분류 후 **라벨 검수(사람 확인) 페이지**
- 이미지 전처리(OpenCV) 기반 보조 특징 추출 (예: 에지 검출 후 GPT 보조 판정)