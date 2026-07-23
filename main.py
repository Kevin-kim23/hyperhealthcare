from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
# 💡 방금 우리가 만든 database.py에서 함수와 변수를 가져옵니다!
import database

app = FastAPI(title="마이 헬스 로그 API", version="3.1")

# database.py의 로드 함수를 통해 초기화
records, current_id = database.load_data()

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
    return {"message": "마이 헬스 로그 API - DB 레이어 분리 완료"}

@app.post("/records")
def create_record(record: RecordIn):
    global current_id, records
    
    data = record.model_dump()
    data["id"] = current_id
    
    # [ Day 2 연산 로직 ]
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
        data["warning"] = True
        data["warning_message"] = "⚠️ 고위험 수치가 감지되었습니다."
    else:
        data["warning"] = False
        data["warning_message"] = ""

    # 분리된 database 모듈의 저장 함수 호출!
    records.append(data)
    database.save_data(records)
    
    current_id += 1
    return data

@app.get("/records")
def get_records():
    return {"total_count": len(records), "data": records}

@app.get("/records/{record_id}")
def get_record(record_id: int):
    for r in records:
        if r["id"] == record_id: return r
    raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")

@app.delete("/records/{record_id}")
def delete_record(record_id: int):
    global records
    for r in records:
        if r["id"] == record_id:
            records = [res for res in records if res["id"] != record_id]
            # 분리된 database 모듈의 저장 함수 호출!
            database.save_data(records)
            return {"message": f"ID {record_id} 기록이 삭제되었습니다."}
    raise HTTPException(status_code=404, detail="삭제할 기록이 없습니다.")