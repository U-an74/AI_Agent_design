
import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv


# 1. 환경변수 로드
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


# 2. 서비스 계정 키 경로 확인
credentials_path = os.getenv("FIREBASE_CREDENTIALS")

if not credentials_path:
    raise ValueError("FIREBASE_CREDENTIALS 환경변수가 설정되지 않았습니다.")

# backend 폴더 기준으로 실제 파일 경로 생성
credentials_path = (BASE_DIR / credentials_path).resolve()

if not credentials_path.is_file():
    raise FileNotFoundError(
        f"Firebase 서비스 계정 키를 찾을 수 없습니다: {credentials_path}"
    )


# 3. Firebase Admin SDK 초기화
if not firebase_admin._apps:
    cred = credentials.Certificate(str(credentials_path))
    firebase_admin.initialize_app(cred)


# 4. Firestore 클라이언트 생성
db = firestore.client()


print("Firebase 연결 모듈 초기화 완료!")
