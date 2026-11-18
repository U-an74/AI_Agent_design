
from datetime import date as datetime_date

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from firebase import db

from collections import Counter
from statistics import mean
from datetime import datetime


app = FastAPI(
    title="AI Lifestyle Manager API",
    description="수면 및 운동 시계열 데이터 관리 API",
    version="1.0.0"
)

# 개발 단계 CORS 설정
# 실제 배포 시에는 Vercel 프론트엔드 주소만 허용하도록 변경
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 1. 데이터 입력 검증 모델
class LifestyleData(BaseModel):
    date: str = Field(
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="날짜 (YYYY-MM-DD)"
    )
    sleep_start_time: str = Field(
        pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$",
        description="수면 시작 시간 (HH:MM)"
    )
    sleep_minutes: int = Field(ge=0, le=1440)
    exercise_type: str = Field(min_length=1, max_length=50)
    exercise_minutes: int = Field(ge=0, le=1440)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value):
        datetime_date.fromisoformat(value)
        return value

    @field_validator("exercise_type")
    @classmethod
    def validate_exercise_type(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("운동 종류를 입력해야 합니다.")
        return value


# 2. API 응답 모델
class LifestyleDataResponse(LifestyleData):
    id: str


# Firestore 컬렉션 지정
data_collection = db.collection("data")


# 3. 서버 상태 확인
@app.get("/")
def root():
    return {"message": "AI Lifestyle Manager API is running"}


# 4. 데이터 추가 (CREATE)
@app.post("/api/data", response_model=LifestyleDataResponse, status_code=201)
def create_data(data: LifestyleData):

    # 동일 날짜 데이터가 이미 있는지 확인
    existing_docs = (
        data_collection
        .where("date", "==", data.date)
        .limit(1)
        .stream()
    )

    if next(existing_docs, None):
        raise HTTPException(
            status_code=409,
            detail="해당 날짜의 데이터가 이미 존재합니다."
        )

    # Firestore 자동 문서 ID 생성
    doc_ref = data_collection.document()
    doc_ref.set(data.model_dump())

    return {
        "id": doc_ref.id,
        **data.model_dump()
    }


# 5. 전체 데이터 조회 (READ)
@app.get("/api/data", response_model=list[LifestyleDataResponse])
def get_all_data():

    docs = data_collection.order_by("date").stream()

    result = []

    for doc in docs:
        result.append({
            "id": doc.id,
            **doc.to_dict()
        })

    return result


# 6. 데이터 수정 (UPDATE)
@app.put("/api/data/{data_id}", response_model=LifestyleDataResponse)
def update_data(data_id: str, data: LifestyleData):

    doc_ref = data_collection.document(data_id)

    # 수정 대상 데이터 존재 여부 확인
    if not doc_ref.get().exists:
        raise HTTPException(
            status_code=404,
            detail="수정할 데이터를 찾을 수 없습니다."
        )

    # 다른 문서에 동일 날짜가 있는지 확인
    existing_docs = (
        data_collection
        .where("date", "==", data.date)
        .limit(2)
        .stream()
    )

    for doc in existing_docs:
        if doc.id != data_id:
            raise HTTPException(
                status_code=409,
                detail="해당 날짜의 데이터가 이미 존재합니다."
            )

    # 전체 필드 수정
    doc_ref.set(data.model_dump())

    return {
        "id": data_id,
        **data.model_dump()
    }


# 7. 데이터 삭제 (DELETE)
@app.delete("/api/data/{data_id}")
def delete_data(data_id: str):

    doc_ref = data_collection.document(data_id)

    # 삭제 대상 데이터 존재 여부 확인
    if not doc_ref.get().exists:
        raise HTTPException(
            status_code=404,
            detail="삭제할 데이터를 찾을 수 없습니다."
        )

    doc_ref.delete()

    return {
        "message": "데이터가 삭제되었습니다.",
        "id": data_id
    }


# 8. 시계열 데이터 요약 (SUMMARY)
@app.get("/api/data/summary")
def get_data_summary():

    # Firestore 전체 데이터 조회
    docs = data_collection.stream()

    records = []

    for doc in docs:
        records.append(doc.to_dict())

    # 데이터가 없는 경우
    if not records:
        raise HTTPException(
            status_code=404,
            detail="요약할 데이터가 없습니다."
        )

    # 날짜 기준 오름차순 정렬
    records.sort(key=lambda x: x["date"])

    # 분석 대상 데이터 추출
    sleep_values = [r["sleep_minutes"] for r in records]
    exercise_values = [r["exercise_minutes"] for r in records]

    # 수면 시작 시간이 목표 시간대(23:00~03:00)에 포함되는지 확인
    target_bedtime_count = 0

    for record in records:
        hour, minute = map(
            int,
            record["sleep_start_time"].split(":")
        )

        bedtime_minutes = hour * 60 + minute

        if bedtime_minutes >= 23 * 60 or bedtime_minutes <= 3 * 60:
            target_bedtime_count += 1

    total_count = len(records)

    target_bedtime_rate = round(
        target_bedtime_count / total_count * 100, 1
    )

    # 운동 종류별 횟수
    exercise_counts = Counter(
        r["exercise_type"] for r in records
    )

    # 최근 7일과 그 이전 7일 비교
    recent_records = records[-7:]
    previous_records = records[-14:-7]

    recent_target_count = sum(
        1 for r in recent_records
        if (
            int(r["sleep_start_time"].split(":")[0]) * 60
            + int(r["sleep_start_time"].split(":")[1])
        ) >= 23 * 60
        or (
            int(r["sleep_start_time"].split(":")[0]) * 60
            + int(r["sleep_start_time"].split(":")[1])
        ) <= 3 * 60
    )

    previous_target_count = sum(
        1 for r in previous_records
        if (
            int(r["sleep_start_time"].split(":")[0]) * 60
            + int(r["sleep_start_time"].split(":")[1])
        ) >= 23 * 60
        or (
            int(r["sleep_start_time"].split(":")[0]) * 60
            + int(r["sleep_start_time"].split(":")[1])
        ) <= 3 * 60
    )

    recent_rate = (
        recent_target_count / len(recent_records) * 100
        if recent_records else 0
    )

    previous_rate = (
        previous_target_count / len(previous_records) * 100
        if previous_records else 0
    )

    rate_difference = round(recent_rate - previous_rate, 1)

    if rate_difference > 0:
        bedtime_trend = "증가"
    elif rate_difference < 0:
        bedtime_trend = "감소"
    else:
        bedtime_trend = "유지"

    # 최종 요약 결과
    return {
        "period": {
            "start_date": records[0]["date"],
            "end_date": records[-1]["date"]
        },
        "total_count": total_count,

        "sleep_summary": {
            "average_minutes": round(mean(sleep_values), 1),
            "max_minutes": max(sleep_values),
            "min_minutes": min(sleep_values)
        },

        "exercise_summary": {
            "average_minutes": round(mean(exercise_values), 1),
            "max_minutes": max(exercise_values),
            "min_minutes": min(exercise_values),
            "exercise_type_counts": dict(exercise_counts)
        },

        "bedtime_summary": {
            "target_time": "23:00~03:00",
            "target_count": target_bedtime_count,
            "outside_count": total_count - target_bedtime_count,
            "target_rate_percent": target_bedtime_rate
        },

        "recent_bedtime_trend": {
            "comparison": "최근 7개 기록 vs 이전 7개 기록",
            "recent_rate_percent": round(recent_rate, 1),
            "previous_rate_percent": round(previous_rate, 1),
            "difference_percentage_points": rate_difference,
            "trend": bedtime_trend
        }
    }
