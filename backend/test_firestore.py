
from firebase import db

# 실제 CSV의 첫 4개 데이터
test_data = [
    {
        "date": "2025-01-01",
        "sleep_start_time": "00:45",
        "sleep_minutes": 425,
        "exercise_type": "걷기",
        "exercise_minutes": 30
    },
    {
        "date": "2025-01-02",
        "sleep_start_time": "00:15",
        "sleep_minutes": 455,
        "exercise_type": "요가",
        "exercise_minutes": 35
    },
    {
        "date": "2025-01-03",
        "sleep_start_time": "22:35",
        "sleep_minutes": 445,
        "exercise_type": "걷기",
        "exercise_minutes": 35
    },
    {
        "date": "2025-01-04",
        "sleep_start_time": "23:45",
        "sleep_minutes": 415,
        "exercise_type": "요가",
        "exercise_minutes": 25
    }
]

# 1. Firestore 저장
for index, data in enumerate(test_data, start=1):
    doc_id = f"step6_test_{index:03d}"
    db.collection("data").document(doc_id).set(data)
    print(f"저장 완료: {doc_id}")

# 2. Firestore 조회
print("\n===== Firestore 조회 결과 =====")

docs = db.collection("data").stream()

for doc in docs:
    if doc.id.startswith("step6_test_"):
        print(doc.id, doc.to_dict())

print("\nFirestore 저장 및 조회 테스트 완료!")
