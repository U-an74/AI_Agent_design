# AI Lifestyle Manager | AI 생활습관 매니저

> Firebase Firestore에 저장된 개인별 수면·운동 기록을 관리하고, 데이터 요약을 바탕으로 생활습관에 대해 대화하는 AI agent입니다.

<br>

## 1. 프로젝트 소개

**AI Lifestyle Manager**는 날짜별 수면 및 운동 데이터를 기록·관리하고, 축적된 데이터를 분석하여 개인의 생활습관을 이해하도록 돕는 웹 서비스입니다. 
<br>
사용자는 브라우저에서 기록을 추가·수정·삭제하고, 요약 통계를 확인하며, AI에게 개선 방향을 질문할 수 있습니다. 
<br>
AI와 주고받은 대화는 Firestore에 저장되어 이후 다시 불러와 이어서 대화할 수 있습니다.

본 프로젝트는 **시계열 데이터 저장**, **CRUD API**, **데이터 요약 API**, **데이터 기반 AI 채팅**, **대화 이력 저장**을 하나의 서비스로 통합하는 것을 목표로 합니다. 

<br>

## 2. 서비스 및 저장소 링크

| 구분 | URL |
| --- | --- |
| 프론트엔드 (Vercel) | https://aiagentdesign.vercel.app |
| 백엔드 API (Render) | https://ai-lifestyle-manager-api.onrender.com |
| Swagger API 문서 | https://ai-lifestyle-manager-api.onrender.com/docs |
| GitHub 저장소 | https://github.com/U-an74/AI_Agent_design |

> **참고:** Render 무료 인스턴스는 유휴 상태에서 중지될 수 있어 첫 API 요청이 지연될 수 있습니다. 프론트엔드는 데이터 로딩 및 연결 오류 메시지를 표시하며, 첫 접속 시 응답이 지연되면 다시 시도해 주세요.

<br>

## 3. 주요 기능

### 3.1 데이터 기반 AI 채팅

- 사용자의 질문에 저장된 생활습관 **요약 통계**를 반영하여 AI 답변 생성
- 새 대화 시작 및 동일 대화 내 후속 질문 지원
- 최근 대화 메시지를 컨텍스트로 전달하여 문맥 유지
- 응답 대기 상태 및 오류 메시지 표시
- 질문과 답변을 Firestore에 자동 저장

### 3.2 생활습관 데이터 관리 (CRUD)

- 날짜별 수면·운동 기록 조회, 추가, 수정, 삭제
- 입력 필드: `date`, `sleep_start_time`, `sleep_minutes`, `exercise_type`, `exercise_minutes`
- 동일 날짜 중복 등록 방지 및 입력값 검증
- 화면에서 날짜/운동 종류 검색

### 3.3 생활습관 요약 분석

- 데이터 기간 및 총 기록 수
- 평균·최대·최소 수면 시간
- 평균·최대·최소 운동 시간 및 운동 종류별 횟수
- 목표 취침 시간대(23:00~03:00) 준수율
- 최근 7개 기록과 이전 7개 기록의 취침 패턴 비교

### 3.4 대화 기록 관리

- AI 대화 기록 목록 조회
- 이전 대화 및 메시지 불러오기
- 기존 대화에서 후속 질문 이어가기
- 필요 없는 대화 기록 삭제

<br>

## 4. 기술 스택

| 영역 | 기술 |
| --- | --- |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| Database | Firebase Cloud Firestore |
| AI 모델 | Codyssey API (gpt-5.4) |
| AI 연동 | OpenAI Python SDK (Chat Completions API 호환 인터페이스) |
| Frontend 배포 | Vercel (정적 사이트) |
| Backend 배포 | Render (Web Service) |
| 버전 관리 | Git, GitHub |

프론트엔드는 React나 Vue 등의 프레임워크 없이 **순수 HTML/CSS/JavaScript**로 작성했습니다.

<br>

## 5. 시스템 구성

```text
사용자 브라우저
    │
    ▼
Vercel ── HTML / CSS / Vanilla JavaScript
    │
    │ HTTPS REST API 요청
    ▼
Render ── FastAPI (Python)
    ├── Firebase Firestore ── 날짜별 생활습관 데이터 및 대화 기록 저장
    └── AI 채팅 API ── 요약 통계와 대화 문맥을 전달해 답변 생성
```

AI 채팅 흐름은 **질문 입력 → FastAPI에서 Firestore 통계 요약 → AI 모델에 요약·대화 문맥 전달 → 답변 생성 → 대화 저장 → 화면 표시** 순서입니다.

<br>

## 6. 프로젝트 구조

```text
AI-lifestyle-manager/
├── backend/
│   ├── main.py               # FastAPI 엔드포인트 및 AI 채팅
│   ├── firebase.py           # Firebase Admin SDK 초기화
│   ├── requirements.txt      # Python 의존성
│   ├── .env.example          # 환경 변수 예시
│   └── .python-version       # Render Python 버전
├── frontend/
│   ├── index.html            # 메인 화면
│   ├── style.css             # UI 스타일
│   ├── app.js                # API 통신 및 사용자 기능
│   ├── config.js             # 로컬 API 주소 설정
│   └── build.mjs             # Vercel 빌드 시 환경 변수 주입
├── .gitignore
└── README.md
```

로컬 개발 시에는 별도 `secrets/` 폴더에 Firebase 서비스 계정 키 파일을 두며, **비밀 키와 `.env` 파일은 Git에 포함하지 않습니다.**

<br>

## 7. 로컬 실행 방법

### 7.1 저장소 복제 및 백엔드 설치

```bash
git clone https://github.com/U-an74/AI_Agent_design.git
cd AI_Agent_design
python -m venv .venv
```

가상환경 활성화:

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

의존성 설치 및 서버 실행:

```bash
pip install -r backend/requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

- 로컬 백엔드: http://127.0.0.1:8000
- 로컬 Swagger: http://127.0.0.1:8000/docs

### 7.2 백엔드 환경 변수

`backend/.env.example`을 참고해 `backend/.env` 파일을 만들고 본인의 인증 정보를 설정합니다.

```dotenv
# 로컬: backend/ 기준 상대경로
FIREBASE_CREDENTIALS=../secrets/firebase-service-account.json

# AI API 설정
OPENAI_API_KEY=YOUR_API_KEY
OPENAI_MODEL=gpt-5.4
# OpenAI 호환 API를 사용할 경우 사용할 엔드포인트 예시
OPENAI_BASE_URL=https://copa.codyssey.kr/v1
```

Firebase 서비스 계정 JSON 파일은 로컬의 `secrets/firebase-service-account.json`에 별도로 보관합니다. Render에서는 파일 경로 대신 **`FIREBASE_SERVICE_ACCOUNT_JSON`** 환경 변수에 서비스 계정 JSON 문자열을 등록할 수 있습니다.

> **AI API 설정:** OpenAI Python SDK는 `OPENAI_BASE_URL` 환경 변수를 지원하므로, 현재 코드처럼 클라이언트 생성 시 `base_url`을 별도로 명시하지 않아도 해당 값을 사용합니다. 로컬과 Render에서 동일한 COPA 엔드포인트를 쓰려면 `OPENAI_BASE_URL`을 설정하세요. API 키는 절대 GitHub나 브라우저 코드에 포함하지 마세요.

### 7.3 프론트엔드 실행

별도 터미널에서 저장소 최상위 폴더로 이동한 후 실행합니다.

```bash
cd frontend
python -m http.server 5500
```

브라우저에서 http://localhost:5500 접속.

- `frontend/config.js` 또는 `app.js`의 API 주소 설정은 사용하려는 백엔드 주소에 맞게 구성합니다.
- 현재 프론트엔드는 배포된 Render API 주소를 기본값으로 사용합니다.
- 로컬 FastAPI에 연결하려면 API 주소를 `http://127.0.0.1:8000`으로 변경하고, 백엔드 CORS 허용 출처 설정을 확인하세요.

<br>

## 8. Vercel / Render 배포 설정

### 8.1 Vercel — 프론트엔드

| 항목 | 설정값 |
| --- | --- |
| Repository | `U-an74/AI_Agent_design` |
| Root Directory | `frontend` |
| Application Preset | `Other` |
| Build Command | `node build.mjs` |
| Output Directory | `dist` |
| 환경 변수 | `API_BASE_URL=https://ai-lifestyle-manager-api.onrender.com` |

`build.mjs`는 배포 시 `API_BASE_URL`을 읽어 `dist/config.js`를 생성합니다. 정적 웹페이지의 JavaScript는 Vercel 환경 변수를 직접 읽을 수 없으므로, **빌드 시점에 공개 API URL만 브라우저용 설정 파일로 전달**합니다.

### 8.2 Render — 백엔드

- 서비스 유형: Python Web Service
- Root Directory: `backend`
- 설치 명령 예시: `pip install -r requirements.txt`
- 실행 명령 예시: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- 환경 변수: `FIREBASE_SERVICE_ACCOUNT_JSON`, `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`
- CORS 허용 출처: `https://aiagentdesign.vercel.app`, `http://localhost:5500`, `http://127.0.0.1:5500`

※**주의:** Firebase 인증 JSON과 AI API 키 등 비밀 정보는 Render 환경 변수에서만 관리하고, 프론트엔드 또는 GitHub에 공개하지 않습니다.

<br>

## 9. API 목록

| Method | Endpoint | 설명 |
| --- | --- | --- |
| GET | `/` | 서버 상태 확인 |
| POST | `/api/data` | 생활습관 기록 추가 |
| GET | `/api/data` | 생활습관 기록 전체 조회 |
| PUT | `/api/data/{data_id}` | 생활습관 기록 수정 |
| DELETE | `/api/data/{data_id}` | 생활습관 기록 삭제 |
| GET | `/api/data/summary` | 데이터 요약 통계 |
| POST | `/api/conversations` | 대화 기록 생성 |
| GET | `/api/conversations` | 대화 목록 조회 |
| GET | `/api/conversations/{conversation_id}` | 개별 대화 및 메시지 조회 |
| DELETE | `/api/conversations/{conversation_id}` | 대화 기록 삭제 |
| POST | `/api/chat` | 데이터 기반 AI 채팅 |

총 **11개 API 동작**을 FastAPI Swagger에서 확인할 수 있습니다.

<br>

## 10. 데이터 구성 및 검증 결과

### 10.1 샘플 데이터

테스트용 생활습관 기록 **100개**(2025-01-01 ~ 2025-04-10)를 Firestore에 저장했습니다.

| 지표 | 검증 당시 값 |
| --- | --- |
| 전체 기록 수 | 100개 |
| 평균 수면 시간 | 430.9분 (약 7시간 11분) |
| 평균 운동 시간 | 22.7분 |
| 운동하지 않은 날 | 37일 (37%) |
| 목표 취침 시간대 준수율 | 88% |
| 최근 7개 vs 이전 7개 취침 패턴 | 100% vs 100%, 유지 |

위 수치는 테스트용 샘플 데이터 기준이며 실제 기록 추가·수정·삭제에 따라 변할 수 있습니다.

### 10.2 기능 테스트

| 구분 | 테스트 결과 |
| --- | --- |
| STEP 11 — Swagger 및 예외 처리 | CRUD, 요약 API, 대화 이력, AI 채팅, 입력 검증 확인 |
| STEP 12 — Render 배포 | 배포 후 API, Firestore 연결, AI 채팅 동작 확인 |
| STEP 13 — 로컬 프론트엔드 | AI 첫 질문·후속 질문, CRUD, 이전 대화 불러오기 **6/6 통과** |
| STEP 14 — Vercel 배포 | 실제 배포 주소에서 AI 채팅, CRUD, 이전 대화 불러오기, 기록 수 복원 **7/7 통과** |

- 테스트를 위해 추가한 임시 데이터는 삭제했으며, 검증 종료 시 샘플 기록 수 **100개**를 확인했습니다.
- 각 STEP별 테스트 절차 등 상세 내용은 아래 「12.개발 작업 로그 📒」에서 확인할 수 있습니다.

<br>

## 11. 시연 화면

### AI 채팅 및 데이터 기반 답변
![AI 채팅 화면](docs/screenshots/ai-chat.png)

### 데이터 추가·수정·삭제
![CRUD 화면](docs/screenshots/data-crud.png)

### 이전 대화 불러오기
![대화 기록 화면](docs/screenshots/conversation-history.png)

<br>

## 12. 개발 작업 로그 📒

본 프로젝트는 기획부터 데이터 설계, Firebase Firestore 연동, FastAPI 기반 백엔드 개발, GPT API 통합, 프론트엔드 구현 및 클라우드 배포까지 단계별로 개발하였습니다.

상세 개발 과정은 Notion 작업 로그에 정리하였으며, 다음과 같은 내용을 확인할 수 있습니다.

- STEP 1~15 단계별 구현 과정 및 진행 현황
- 주요 API 기능 구현 및 Swagger 테스트
- GPT API 연동, 오류 처리 및 문제 해결 과정
- Render 백엔드 및 Vercel 프론트엔드 배포 과정
- 최종 기능 검증 결과

**[AI Lifestyle Manager — Notion 개발 작업 로그](https://exuberant-cuckoo-0b8.notion.site/AI-Agent-AI-41a631db7fe08067a7edd1554663fc7d)** 

<br>

## 13.과제를 통해 배운 점 📚

본 프로젝트를 통해 시계열 데이터의 저장과 분석부터 AI 연동, 웹서비스 구현 및 클라우드 배포까지 전체 개발 과정을 경험할 수 있었습니다.
<br>
특히 각 기술의 개별적 사용에서 나아가, 데이터베이스·백엔드·프론트엔드·AI가 하나의 서비스로 연결되는 구조에 대한 이해가 깊어졌습니다.

### 1. 시계열 데이터 분석 및 요약 정보 활용
무료버전 Chatgpt를 활용하여 가상의 날짜별 수면 시간과 운동 기록으로 구성된 100개의 시계열 데이터를 제작했고,  
<br>
제작한 데이터를 Firebase Firestore에 저장하여 평균·최대·최소·횟수·최근 추세 등의 통계를 계산했습니다. 
<br>
이 과정에서 단순 데이터 저장에서 나아가, 목적에 맞게 요약해서 사용자에게 의미 있는 정보로써 제공하는 과정이 중요하다는 것을 배울 수 있었습니다. 

### 2. FastAPI 기반 백엔드 구조 이해
FastAPI를 활용하여 데이터 CRUD, 통계 요약, 대화 기록 관리, AI 채팅 기능을 API로 구현했습니다. 
<br>
`main.py`에서 API 엔드포인트와 요청 처리 흐름을 구성하고, `firebase.py`에서 데이터베이스 초기화 및 연결 기능을 분리하면서 
<br>
기능별 역할을 구분하는 설계의 필요성을 이해했습니다. 
<br>
다만, 프로젝트 규모가 작아 라우터와 서비스 계층을 별도 모듈로 분리하는 작업에 대해서는「14-2.향후 개선 방향」에서 과제로 남겨두었습니다. 

### 3. Pydantic을 활용한 데이터 검증 및 예외 처리
Pydantic 모델을 사용하여 API 요청 데이터의 필수 항목, 자료형, 허용 범위 등을 검증하는 방법을 익혔습니다. 
<br>
Swagger를 통해 정상 요청뿐 아니라 잘못된 입력값, 중복 데이터, 존재하지 않는 데이터 등을 테스트하면서 아래에 대해서도 이해할 수 있었습니다. 
- HTTP 상태 코드 `404`, `409`, `422`의 의미 
- 적절한 예외 처리 방식
<br>
이를 통해 입력값 검증이 데이터 무결성과 서비스 안정성에 중요한 역할을 한다는 점을 배울 수 있었습니다. 

### 4. Firebase Firestore 기반 데이터 관리
Firestore의 컬렉션과 문서 구조를 이해하고, 생활습관 데이터와 AI 대화 기록을 각각 저장하고 관리하는 기능을 구현하였습니다.
<br>
데이터의 생성(C), 조회(R), 수정(U), 삭제(D)를 직접 구현하고 프론트에서 테스트하며 데이터베이스와 API가 연결되는 과정을 학습하였고,
<br>
특히 데이터 수정 및 삭제 이후 실제 Firestore에 변경 사항이 반영되는 것을 검증하면서 데이터 관리 흐름도 이해할 수 있었습니다. 

### 5. AI 컨텍스트 주입 및 대화 기록 관리
Codyssey API와 OpenAI Python SDK를 연동하여 사용자 질문에 답변하는 AI 채팅 기능을 구현하였습니다. 
<br>
이 과정에서 Firestore에 저장된 데이터의 요약 통계를 시스템 프롬프트에 포함하여 GPT에 전달하는 핵심 기능, 
<br>
**컨텍스트 주입(Context Injection)** 방식을 학습하였고,
<br>
대화 ID를 활용하여 이전 대화를 이어가고 질문과 답변은 Firestore에 불러와서 저장하는 구조도 이해할 수 있었습니다. 

### 6. 클라우드 배포 및 환경 설정 관리
Render에 FastAPI 백엔드를, Vercel에 HTML/CSS/JavaScript 기반 프론트엔드를 배포하면서 로컬 개발 환경과 실제 운영 환경의 차이를 경험하였습니다. 
<br>
서로 다른 도메인에서 API를 호출하기 위한 아래 관리법을 학습하였고,
- CORS 설정
- 환경 변수를 통한 API 서버 주소 관리
- Firebase 인증 정보와 API 키의 안전한 보관 방법
<br>
Render 무료 서비스의 콜드스타트 특성을 이해하여 프론트엔드에서 로딩 상태와 연결 안내 문구를 제공하는 방식으로 사용자 경험 개선을 위해 노력했습니다. 

### 7. 통합 테스트와 문제 해결의 중요성
개별 API의 정상 동작 확인에서 나아가, Swagger를 활용한 예외 처리 테스트와 실제 배포 사이트에서의 통합 테스트까지 수행했습니다. 
<br>
AI 채팅, 후속 질문, 데이터 CRUD, 대화 기록 조회 등 주요 기능을 각 구현 단계에서 검증했지만, 기능 구현 이후에도 반복적인 테스트와 오류 분석을 진행했습니다. 

<br>

## 14. 현재 한계점 및 향후 고도화 과제

### 14.1 현재 한계점 — 요약 통계 중심의 AI 분석

현재 서비스는 날짜별 수면 시간과 운동 종류·시간이 연결된 **원본 데이터**를 Firestore에 저장합니다. 그러나 AI 채팅에서는 원본 기록 전체를 질문별로 탐색하는 대신, 백엔드가 미리 계산한 **전체 요약 통계**를 주로 전달합니다.

따라서 **“운동한 날과 운동하지 않은 날의 평균 수면 시간은 얼마나 차이가 나는가?”** 와 같이 날짜별 기록을 묶어 새로 계산해야 하는 질문에는 정확한 수치를 바로 제시하기 어렵습니다. 원본 데이터가 없는 것이 아니라, **질문에 맞춰 원본 데이터를 조회·집계하는 기능이 아직 구현되지 않은 것**이 한계입니다.

### 14.2 향후 개선 방향 

#### 1. 질문 기반 동적 데이터 분석

향후 다음 흐름으로 기능을 확장(고도화)할 계획입니다.

1. **질문 의도 분석:** 자연어 질문에서 기간, 비교 대상, 통계 항목 등을 추출
2. **동적 데이터 조회:** 필요한 날짜별 Firestore 원본 기록을 선택적으로 조회
3. **통계 자동 계산:** 운동 유무별 평균 수면, 운동 종류별 비교, 기간별 변화량 등을 백엔드에서 정확하게 계산
4. **근거 기반 AI 답변:** 계산된 통계와 분석 조건을 GPT에 전달해 수치와 해석을 함께 제공

이를 통해, 미리 정의된 요약 지표를 설명하는 수준을 넘어 다양한 개인 맞춤 분석 질문에 대응할 수 있도록 발전시키고자 합니다.

#### 2. 백엔드 구조 모듈화 (라우터·서비스 계층 분리)

- 한계점
현재 백엔드는 main.py를 중심으로 API 엔드포인트와 주요 비즈니스 로직이 구현되어 있으며, Firebase 초기화 및 연결 기능은 firebase.py로 별도 분리되어 있습니다. 
그러나 API 라우터와 서비스 계층이 독립적인 모듈로 분리되어 있지 않아, 기능이 확장될 경우 코드 유지보수와 테스트가 복잡해질 수 있다는 한계점이 존재합니다. 

- 개선 방향
FastAPI의 APIRouter를 활용하여 데이터 관리, 통계 분석, 대화 관리, AI 채팅 기능을 라우터별로 분리하고, 데이터 처리 및 비즈니스 로직은 별도의 서비스 모듈로 구성할 계획입니다.
이를 통해 코드의 재사용성, 유지보수성, 테스트 편의성 및 확장성을 개선하고자 합니다. 

### 14.3 추가 개선 방향

- 사용자별 로그인·인증 및 데이터 접근 권한 분리
- 데이터 시각화 및 기간별 추세 비교 확대
- 개인별 목표 설정과 주기적인 생활습관 자동 피드백
- 운영 환경에서의 데이터 보호 및 보안 정책 강화

> **보안 및 사용 범위:** 현재 프로젝트는 학습·시연 목적의 프로토타입이며, 사용자별 인증/권한 분리가 구현된 서비스로 간주해서는 안 됩니다. 공개 배포 환경에서는 실제 민감한 건강정보가 아닌 **테스트용 또는 합성 데이터**만 사용하세요. AI 답변은 의료적 진단이나 치료 조언을 대체하지 않습니다.

---

**개발 목적:** 데이터 기반 개인 AI 서비스 구축 실습
