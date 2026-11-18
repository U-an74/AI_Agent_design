
import csv
from pathlib import Path

from firebase import db


# CSV 파일 경로
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "100day_lifestyle_data.csv"

# Firestore 컬렉션
collection = db.collection("data")


def import_data():

    # CSV 파일 존재 여부 확인
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV 파일을 찾을 수 없습니다: {CSV_PATH}"
        )

    # 기존 Firestore 데이터의 날짜 수집
    existing_docs = collection.stream()

    existing_dates = {
        doc.to_dict().get("date")
        for doc in existing_docs
    }

    added_count = 0
    skipped_count = 0

    batch = db.batch()
    batch_count = 0

    # CSV 읽기
    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as file:

        reader = csv.DictReader(file)

        required_columns = {
            "date",
            "sleep_start_time",
            "sleep_minutes",
            "exercise_type",
            "exercise_minutes"
        }

        if not required_columns.issubset(reader.fieldnames or []):
            raise ValueError("CSV 컬럼 구성이 올바르지 않습니다.")

        for row in reader:

            data = {
                "date": row["date"].strip(),
                "sleep_start_time": row["sleep_start_time"].strip(),
                "sleep_minutes": int(row["sleep_minutes"]),
                "exercise_type": row["exercise_type"].strip(),
                "exercise_minutes": int(row["exercise_minutes"])
            }

            # 이미 등록된 날짜는 건너뛰기
            if data["date"] in existing_dates:
                skipped_count += 1
                continue

            # 날짜를 문서 ID로 사용해 중복 등록 방지
            doc_id = data["date"]

            doc_ref = collection.document(doc_id)
            batch.set(doc_ref, data)

            existing_dates.add(data["date"])

            added_count += 1
            batch_count += 1

            # Firestore batch 제한보다 여유 있게 분할 저장
            if batch_count == 400:
                batch.commit()
                batch = db.batch()
                batch_count = 0

    # 남은 데이터 저장
    if batch_count > 0:
        batch.commit()

    print("===== 데이터 등록 결과 =====")
    print(f"신규 등록: {added_count}개")
    print(f"중복 제외: {skipped_count}개")
    print(f"CSV 데이터 처리 완료")


if __name__ == "__main__":
    import_data()
