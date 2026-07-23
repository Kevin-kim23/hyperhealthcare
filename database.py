import json
import os

DATA_FILE = "data.json"

# 하드디스크 로드 함수
def load_data():
    if not os.path.exists(DATA_FILE):
        return [], 1
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return [], 1
            saved_records = json.loads(content)
            next_id = max([r["id"] for r in saved_records]) + 1 if saved_records else 1
            return saved_records, next_id
    except Exception:
        return [], 1

# 하드디스크 저장 함수
def save_data(records_to_save):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records_to_save, f, ensure_ascii=False, indent=4)