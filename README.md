# 🚗 자동차 불량 분류 보조 시스템 (VisionQC)

자동차 외장 불량 이미지를 **PyQt5 GUI**로 업로드 → **GPT 기반 분류/설명** → **SQLite DB 저장·검색**까지 한 번에 처리하는 **품질 관리 보조 시스템**입니다.  
GPT 모델 기반의 비전 분석 보조 툴로, **불량 분류·설명 자동화 + 기록·검색 편의성 강화**에 초점을 맞춘 프로젝트입니다.

---

## 📌 주제 및 선정배경
자동차 산업에서는 품질 관리(QA/QC)를 위해 불량 부품 이미지를 빠르게 분류하고 기록하는 것이 중요합니다.  
<strong>자동차 품질 관리 보조 시스템(VisionQC)</strong>는 GPT 기반 시각 인식 모델을 활용하여 불량 이미지를 자동 분류·설명하고, SQLite DB에 체계적으로 저장함으로써 품질 데이터의 축적과 분석을 용이하게 하는 것을 목표로 합니다.

---

## 🎯 목표
- 카메라로 촬영한 자동차 부품 이미지를 GPT를 통해 자동 분석  
- **스크래치, 균열, 오염, 납땜 불량, 변형, 정렬불량, 부품 누락 등** 유형 분류 및 설명 제공  
- 결과를 SQLite DB에 저장하고 **PyQt5 GUI**를 통해 검색·조회  

---

## 🧩 주요 기능

| 구분 | 설명 |
|------|------|
| 🖼️ **이미지 업로드 및 분류(Classify)** | 단일/다중 이미지 업로드 후 GPT 기반 분류 수행 |
| 💾 **DB 저장 (SQLite3)** | 결과를 자동 저장 및 불러오기 |
| 🔍 **검색 및 삭제** | 툴바를 통한 DB 검색 / 선택 행 삭제 |
| 📊 **통계 대시보드** | 불량 데이터의 통계 분석 및 시각화 (4개 탭) |
| 💾 **Save PNG / Export CSV** | 그래프 또는 데이터 내보내기 기능 |
| 📂 **Export DB (CSV)** | 전체 DB를 CSV 파일로 저장 |

---

## 🛠 진행 상황 (2025-10-05 기준)
- [x] **단일/폴더 업로드** → GPT 분류 및 설명 출력 → DB 저장  
- [x] **DB 스키마 정리**: `results` 단일 테이블
- [x] **검색 기능 추가**: 라벨, 키워드, 날짜 범위 필터링
- [x] **삭제 기능 추가**: 선택된 행 삭제 후 테이블 갱신
- [x] **중복 저장 방지**: UNIQUE 인덱스 + `INSERT OR IGNORE` / UPSERT 적용
- [x] **CarDD 샘플링 스크립트 추가** `copy_cardd_samples.py` (실행 시 대상 폴더 비우기 옵션 지원)
- [x] **통계 대시보드 테스트용 DB 생성 스크립트 추가** `make_test_db.py`
- [x] **통계 대시보드 4탭 구성** (`Defect Distribution`, `Daily Trend`, `Additional Metrics`, `Location & Action`)   
- [x] **통계 대시보드 Image/CSV Export 기능**
- [x] **툴바 Export DB (CSV)** — `app.db` 전체를 CSV 파일로 내보내기  

---

## 🧩 사용 기술
- **Python**
- **PyQt5** — GUI 구성  
- **OpenAI API (gpt-4o-mini)** — 불량 유형 및 설명 자동 생성  
- **SQLite3** — 경량 데이터베이스  
- **dotenv (.env)** — 환경 변수 관리  
- **Matplotlib** — 통계 대시보드 및 시각화
- **Pandas** - DB를 DataFrame으로 변환, CSV 내보내기 기능
- **Numpy** - 그래프 데이터 전처리

---

## ⚙️ .env 설정
루트 디렉토리에 `.env` 파일 생성:  

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
DB_PATH=app.db
👉 DB_PATH는 생략 시 app.db 기본값을 사용합니다.
👉 API Key는 OpenAI 계정에서 발급받아야 합니다.
```

---

## 📂 데이터셋 출처

본 프로젝트에서는 **CarDD (Car Damage Dataset)** 를 활용하여 GPT-4o mini 기반 분류 실험을 진행합니다.

CarDD는 차량 외장 손상 이미지 약 4,000장을 포함하고 있으며, 스크래치, 찌그러짐, 균열, 변색, 오염 등 다양한 불량 유형을 포함합니다.

- [CarDD 공식 페이지](https://cardd-ustc.github.io/?utm_source=chatgpt.com)

---

## 🔁 전체 흐름

1. 이미지 업로드
2. 프롬프트(분류 요청) 전달
3. GPT-API를 통한 불량 유형 분류/설명
4. 결과 출력 및 SQLite DB 저장
5. 검색 기능으로 불량 유형/날짜별 탐색
6. 데이터 시각화

---

## 📷 예시 시나리오

아래는 VisionQC 시스템이 실제로 작동하는 과정을 기반으로 한 예시입니다.  
각 시나리오는 GUI, GPT API, SQLite DB, 대시보드가 서로 어떻게 연동되는지를 보여줍니다.

---

### 🚗 시나리오 1. 라인 작업자가 불량 부품을 분류 및 저장

1. **이미지 업로드**  
   - 사용자가 `Upload Image` 버튼을 누르고 자동차 부품 이미지를 선택합니다.  
   - `gui/main_app.py` → `get_image_file()` 함수가 실행되어 파일 경로를 불러옵니다.  
   - `_set_preview()`를 통해 썸네일 이미지를 GUI에 미리 표시합니다.

2. **GPT 기반 불량 분류 요청**  
   - 사용자가 `Classify` 버튼을 누르면,  
     `api/openai_api.py`의 `classify_image()` 함수가 호출되어 GPT-4o mini API로 이미지를 전송합니다.  
   - 프롬프트에는 `util/config.py` 내용에 따라 (`scratch`, `dent`, `crack`, `contamination` 등)이 포함됩니다.

3. **DB 저장**  
   - GPT로 받은 응답(JSON 형태)을 사용자가 `Save` 버튼 클릭 시,  
     `gui/main_app.py`의 `on_save()`가 실행되어 SQLite DB(`app.db`)에 결과를 저장합니다.

4. **결과 출력**  
   - DB의 (`label`, `confidence`, `description` 등)이 GUI에 표시됩니다.
   - 예:  
     ```text
     label : scratch  
     confidence: 0.92  
     description: 표면에 선형 흠집이 있습니다.  
     ```

5. **저장 확인**  
   - “저장 완료” 메시지 표시 후, `gui/stats_view.py`의 테이블에 새 레코드를 반영할 수 있습니다.

---

### 📊 시나리오 2. 품질 엔지니어가 불량 데이터를 검색 및 분석

1. **검색 기능 실행**  
   - `Search` 탭에서 불량 유형(`scratch`, `dent` 등) 또는 기간을 선택하고 `Search` 버튼 클릭.  
   - `gui/main_app.py` → `db/db.py` → `search_results()`가 SQLite에서 해당 조건의 데이터를 불러옵니다.

2. **검색 결과 표시**  
   - 결과는 `QTableWidget`으로 표시되며, 각 행에는 이미지 경로 / 불량유형 / Confidence / 날짜가 표시됩니다.  
   - 특정 행을 더블클릭하면 이미지 미리보기 팝업(QDialog)이 실행됩니다.

3. **통계 분석 (Stats Dashboard)**  
   - 사용자가 `View Results` 탭을 열면,  
     `gui/stats_view.py`가 실행되어 DB의 전체 데이터를 로드합니다.
   - 이후 다음과 같은 시각화가 matplotlib로 렌더링됩니다:
     - **Pie Chart**: 불량 유형, 심각도, 조치(Action) 
     - **Bar Chart**: 심각도(Severity)별 결함 발생 빈도, 위치별 결함 분포
     - **Line Chart**: 일자별 불량 발생 추이

4. **CSV 내보내기**  
   - `Export CSV` 버튼 클릭 시, `on_export_csv()`로 `*.csv` 생성
   - 생성된 파일은 지정한 폴더에 저장됩니다.

---

## 📸 실행 화면 (Execution Screenshots)

### 🖥️ 메인 화면
이미지 업로드 → GPT 분류 → DB 저장 → 결과 표시
![Main UI](./assets/main_ui.png)

### ✅ 분류 결과 예시
자동차 이미지에서 결함을 분석하고 결과를 DB에 저장합니다.
![Classification Result](./assets/classify_result.png)

---

### 📊 통계 대시보드 (Stats Dashboard)
![Stats Dashboard UI](./assets/stats_dashboard.png)

#### 1️⃣ Defect Distribution
심각도(Severity)별 결함 발생 빈도를 나타내는 스택형 바 차트  
![Defect Distribution](./assets/Defect%20Distribution.png)

#### 2️⃣ Daily Trend
일자별 불량 발생 추이를 보여주는 라인 차트  
![Daily Trend](./assets/Daily%20Trend.png)

#### 3️⃣ Additional Metrics
- Defect Type Ratio (Top10)  
- Severity Ratio (A/B/C)
![Additional Metrics](./assets/Additional%20Metrics.png)

#### 4️⃣ Location & Action
위치별 결함 분포 및 조치(Action) 비율 시각화  
![Location Action](./assets/Location_Action.png)

---

### 💾 Export 기능
그래프 저장 및 CSV 내보내기 기능이 구현되어 있습니다.

| 기능 | 설명 | 예시 |
|------|------|------|
| **Save PNG** | 대시보드 이미지를 파일로 저장 | ![Export Image](./assets/export_img_success.png) |
| **Export CSV** | 그래프별 데이터를 CSV 파일로 내보내기 | ![Export CSV](./assets/export_csv_success.png) |

---

### 🗂️ Database 뷰 (결과 테이블)
불량 분류 결과가 SQLite DB(`app.db`)에 저장되며 테이블로 표시됩니다.  
![DB Table](./assets/db_results_table.png)

---

## 🔧 시스템 구성도
```text
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
   ↓
[ 데이터 시각화 ]
```
---

## 📁 디렉토리 구조
```text
Rokey_Project_1/
├── gui/
│   └── __init__.py
│   └── main_app.py
│   └── main_window.py
│   └── stats_view.py
├── api/
│   └── __init__.py
│   └── openai_api.py
├─ assets/
├── db/
│   └── __init__.py
│   └── db.py
├── scripts/
│   └── cardd_sampler.py 
│   └── make_test_db.py
├── utils/
│   └── __init__.py
│   └── config.py
│   └── file_handler.py
├── main.py
├── app.db
├── .env.example
└── requirements.txt
```

---

## 🚀 확장 아이디어

- 이미지 전처리(OpenCV) 기반 보조 특징 추출 (예: 에지 검출 후 GPT 보조 판정)

---

## 📦 requirements.txt
```text
# GUI
PyQt5==5.15.10

# Data & Math
numpy>=1.24.0
pandas>=2.0.0
matplotlib>=3.8.0

# Image Handling
Pillow>=10.0.0

# Environment Variables
python-dotenv>=1.0.0

# OpenAI API
openai>=1.12.0
```

---

## 🚀 실행 방법 (Quickstart)

```bash
git clone https://github.com/mavro7910/Rokey_Project_1.git
cd Rokey_Project_1
pip install -r requirements.txt
cp .env.example .env   # 키 입력
python gui/main_app.py
```

---

## 👨‍💻 개발자
**이광호 (Kwangho Lee)**  
성균관대학교 기계공학부  

- GitHub: [@mavro7910](https://github.com/mavro7910)  
- Email: [kwangho97@g.skku.edu]

---

## 📜 License
이 프로젝트는 [MIT License](./LICENSE)를 따릅니다.

---
