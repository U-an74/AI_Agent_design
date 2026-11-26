
from datetime import date as datetime_date

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from firebase import db

from collections import Counter
from statistics import mean
from datetime import datetime, timezone
from typing import Literal

import os
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv


load_dotenv()

openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=30.0,
    max_retries=1,
)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4")


app = FastAPI(
    title="AI Lifestyle Manager API",
    description="수면 및 운동 시계열 데이터 관리 API",
    version="1.0.0"
)

# 개발 단계 CORS 설정
# 실제 배포 시에는 Vercel 프론트엔드 주소만 허용하도록 변경
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://aiagentdesign.vercel.app",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
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


# 9. 대화 기록 데이터 모델

# 개별 메시지 모델
class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(
        description="메시지 작성자 (user 또는 assistant)"
    )
    content: str = Field(
        min_length=1,
        description="대화 메시지 내용"
    )


# 대화 저장 요청 모델
class ConversationCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=100,
        description="대화 제목"
    )
    messages: list[ConversationMessage] = Field(
        min_length=1,
        description="대화 메시지 목록"
    )

# 10. AI 채팅 요청 모델
class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
        description="사용자 질문"
    )
    conversation_id: str | None = Field(
        default=None,
        description="기존 대화 ID (새 대화는 생략)"
    )


# Firestore 컬렉션 지정
data_collection = db.collection("data")
conversation_collection = db.collection("conversations")


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



# 9. 대화 기록 저장 (CREATE)
@app.post("/api/conversations", status_code=201)
def create_conversation(data: ConversationCreate):

    # 현재 시간 생성
    now = datetime.now(timezone.utc).isoformat()

    # Firestore 자동 문서 ID 생성
    doc_ref = conversation_collection.document()

    # 대화 데이터 저장
    conversation_data = {
        "title": data.title.strip(),
        "created_at": now,
        "updated_at": now,
        "messages": [
            message.model_dump()
            for message in data.messages
        ]
    }

    doc_ref.set(conversation_data)

    return {
        "id": doc_ref.id,
        **conversation_data
    }

# 10. 대화 기록 목록 조회 (READ)
@app.get("/api/conversations")
def get_conversations():

    # Firestore에 저장된 모든 대화 기록 조회
    docs = conversation_collection.stream()

    conversations = []

    for doc in docs:
        conversation_data = doc.to_dict()

        conversations.append({
            "id": doc.id,
            "title": conversation_data.get("title"),
            "created_at": conversation_data.get("created_at"),
            "updated_at": conversation_data.get("updated_at"),
            "message_count": len(conversation_data.get("messages", []))
        })

    # 최근 수정된 대화가 먼저 오도록 정렬
    conversations.sort(
        key=lambda item: item["updated_at"] or "",
        reverse=True
    )

    return {
        "total_count": len(conversations),
        "conversations": conversations
    }

# 개별 대화 기록 조회 (READ)
@app.get("/api/conversations/{conversation_id}")
def get_conversation(conversation_id: str):

    # Firestore에서 해당 문서 조회
    doc = conversation_collection.document(conversation_id).get()

    # 문서가 존재하지 않는 경우
    if not doc.exists:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    # 대화 데이터 반환
    return {
        "id": doc.id,
        **doc.to_dict()
    }


    # 대화 기록 삭제 (DELETE)
@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):

    # Firestore 문서 참조
    doc_ref = conversation_collection.document(conversation_id)

    # 문서 존재 여부 확인
    doc = doc_ref.get()

    # 문서가 존재하지 않는 경우
    if not doc.exists:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    # 대화 기록 삭제
    doc_ref.delete()

    return {
        "message": "Conversation deleted successfully",
        "id": conversation_id
    }


# 10. GPT API 및 컨텍스트 주입
@app.post("/api/chat")
def chat(request: ChatRequest):

    # 1. 기존 데이터 요약 함수 재사용
    summary = get_data_summary()

    # 2. 시스템 프롬프트 구성
    system_prompt = f"""
당신은 AI 생활습관 매니저입니다.

사용자의 수면 및 운동 기록을 분석하여
친절하고 실용적인 답변을 한국어로 제공하세요.

[사용자 생활습관 데이터 요약]
{summary}

[답변 원칙]
1. 실제 데이터에 근거하여 답변하세요.
2. 수면 시간, 운동 시간, 취침 패턴을 활용하세요.
3. 데이터에 없는 정보는 추측하지 마세요.
4. 개선이 필요한 부분은 구체적으로 설명하세요.
5. 의료적 진단이나 확정적인 건강 판단은 하지 마세요.
6. 답변은 이해하기 쉽게 작성하세요.
"""

    # 3. 신규 대화 또는 기존 대화 확인
    now = datetime.now(timezone.utc).isoformat()

    if request.conversation_id:
        doc_ref = conversation_collection.document(
            request.conversation_id
        )
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=404,
                detail="대화 기록을 찾을 수 없습니다."
            )

        conversation = doc.to_dict()
        messages = conversation.get("messages", [])

    else:
        doc_ref = conversation_collection.document()
        messages = []

        conversation = {
            "title": request.message[:50],
            "created_at": now,
            "updated_at": now,
            "messages": []
        }

    # 4. 이전 대화와 현재 질문 구성
    user_message = {
        "role": "user",
        "content": request.message
    }

    ai_input = messages[-10:] + [user_message]


    # 5. OpenAI Chat Completions API 호출
    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                *ai_input
            ],
            max_tokens=1200
        )


        # AI 답변 및 종료 이유 확인
        choice = response.choices[0]
        ai_answer = choice.message.content

        print(f"[GPT FINISH REASON] {choice.finish_reason}")

        if not ai_answer:
            raise HTTPException(
                status_code=502,
                detail="AI 응답 내용이 비어 있습니다."
            )


    except OpenAIError as e:
        print(f"[OpenAI API ERROR] {type(e).__name__}")

        if hasattr(e, "status_code"):
            print(f"STATUS CODE: {e.status_code}")

        if hasattr(e, "body"):
            print(f"ERROR BODY: {e.body}")

        raise HTTPException(
            status_code=502,
            detail="AI 서비스 호출에 실패했습니다."
        )


    # 6. 사용자 질문과 AI 답변 추가
    messages.append(user_message)
    messages.append({
        "role": "assistant",
        "content": ai_answer
    })

    # 7. Firestore에 대화 자동 저장
    conversation["messages"] = messages
    conversation["updated_at"] = now

    doc_ref.set(conversation)

    # 8. 프론트엔드에 결과 반환
    return {
        "conversation_id": doc_ref.id,
        "answer": ai_answer,
        "message_count": len(messages)
    }
