from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="마이 헬스 로그 API", version="1.0")

# 임시 메모리 데이터베이스 역할을 할 리스트와 ID 변수
records = []
current_id = 1

# [Day 1] 요구사항에 맞춘 Pydantic 입력 모델 정의
class RecordIn(BaseModel):
    date: str
    weight: float
    height: float
    systolic: int
    diastolic: int
    blood_sugar: int
    steps: int = 0
    sleep_hours: float = 0.0
    memo: str = ""

@app.get("/")
def read_root():
    return {"message": "마이 헬스 로그 API"}

# [TODO 1] POST /records : 건강 기록 추가
@app.post("/records")
def create_record(record: RecordIn):
    global current_id
    new_record = record.model_dump()
    new_record["id"] = current_id
    
    # Day 1 단계에서는 계산 로직 없이 데이터 저장 및 응답만 진행
    records.append(new_record)
    current_id += 1
    return new_record

# [TODO 2] GET /records : 전체 기록 조회
@app.get("/records")
def get_records():
    return {"total_count": len(records), "data": records}

# [TODO 3] GET /records/{record_id} : 단건 조회 (없으면 404)
@app.get("/records/{record_id}")
def get_record(record_id: int):
    for r in records:
        if r["id"] == record_id:
            return r
    raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")

# [TODO 4] DELETE /records/{record_id} : 기록 삭제
@app.delete("/records/{record_id}")
def delete_record(record_id: int):
    global records
    for r in records:
        if r["id"] == record_id:
            records = [res for res in records if res["id"] != record_id]
            return {"message": f"ID {record_id} 기록이 삭제되었습니다."}
    raise HTTPException(status_code=404, detail="삭제할 기록이 없습니다.")
