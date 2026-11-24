
import os
import json
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv


# 1. 환경변수 로드
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


# 2. Firebase 인증 정보 확인
service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if service_account_json:
    # Render 환경: JSON 문자열을 환경 변수에서 읽기
    service_account_info = json.loads(service_account_json)
    cred = credentials.Certificate(service_account_info)

else:
    # 로컬 환경: 기존 JSON 파일 사용
    credentials_path = os.getenv("FIREBASE_CREDENTIALS")

    if not credentials_path:
        raise ValueError(
            "Firebase 인증 환경변수가 설정되지 않았습니다."
        )

    credentials_path = (BASE_DIR / credentials_path).resolve()

    if not credentials_path.is_file():
        raise FileNotFoundError(
            f"Firebase 서비스 계정 키를 찾을 수 없습니다: {credentials_path}"
        )

    cred = credentials.Certificate(str(credentials_path))


# 3. Firebase Admin SDK 초기화
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)


# 4. Firestore 클라이언트 생성
db = firestore.client()

print("Firebase 연결 모듈 초기화 완료!")
