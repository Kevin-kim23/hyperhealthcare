from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
# 💡 새로 바꾼 sqlite3 기반 database.py 수입!
import database

app = FastAPI(title="마이 헬스 로그 API", version="3.5 (SQL 버전)")

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
    return {"message": "마이 헬스 로그 API - SQLite3 데이터베이스 엔진 가동 중"}

# [POST /records] 수치 연산 후 SQL 서버에 직접 저장
@app.post("/records")
def create_record(record: RecordIn):
    data = record.model_dump()
    
    # [Day 2] 자동 건강 분석 알고리즘 가동
    height_m = data["height"] / 100.0
    bmi = round(data["weight"] / (height_m ** 2), 2) if height_m > 0 else 0.0
    data["bmi"] = bmi
    
    if bmi < 18.5: data["bmi_status"] = "저체중"
    elif bmi < 23.0: data["bmi_status"] = "정상"
    elif bmi < 25.0: data["bmi_status"] = "과체중"
    else: data["bmi_status"] = "비만"
        
    sys, dia = data["systolic"], data["diastolic"]
    if sys < 120 and dia < 80: data["blood_pressure_status"] = "정상"
    elif sys >= 140 or dia >= 90: data["blood_pressure_status"] = "고혈압"
    else: data["blood_pressure_status"] = "전고혈압"
        
    sugar = data["blood_sugar"]
    if sugar < 100: data["blood_sugar_status"] = "정상"
    elif sugar <= 125: data["blood_sugar_status"] = "공복혈당장애(당뇨전단계)"
    else: data["blood_sugar_status"] = "당뇨"
        
    if data["blood_pressure_status"] == "고혈압" or data["blood_sugar_status"] == "당뇨":
        data["warning"] = 1  # SQLite 호환을 위해 정수형(1/0) 처리
        data["warning_message"] = "⚠️ 고위험 수치가 감지되었습니다. 전문의와 상담을 권장합니다."
    else:
        data["warning"] = 0
        data["warning_message"] = ""

    # 💡 메모리 변수 대신 database.py의 SQL 저장 함수에 바로 밀어넣기!
    new_id = database.save_record(data)
    data["id"] = new_id
    
    # 불리언(Boolean) 가독성을 위해 응답 시 변환
    data["warning"] = True if data["warning"] == 1 else False
    return data

# [GET /records] 테이블 전체 행을 SELECT문으로 긁어오기
@app.get("/records")
def get_records():
    sql_records = database.get_all_records()
    # 응답 데이터 가독성 정제
    for r in sql_records:
        r["warning"] = True if r["warning"] == 1 else False
    return {"total_count": len(sql_records), "data": sql_records}

# [GET /records/{record_id}] 특정 행만 WHERE문으로 조회하기
@app.get("/records/{record_id}")
def get_record(record_id: int):
    res = database.get_record_by_id(record_id)
    if not res:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    res["warning"] = True if res["warning"] == 1 else False
    return res

# [DELETE /records/{record_id}] 특정 행을 DELETE문으로 날리기
@app.delete("/records/{record_id}")
def delete_record(record_id: int):
    success = database.delete_record_by_id(record_id)
    if not success:
        raise HTTPException(status_code=404, detail="삭제할 기록이 없습니다.")
    return {"message": f"ID {record_id} 기록이 SQL 데이터베이스에서 영구 삭제되었습니다."}