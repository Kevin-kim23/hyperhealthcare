from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="마이 헬스 로그 API", version="2.0")

# 데이터 임시 저장용 리스트와 고유 ID 변수
records = []
current_id = 1

# [Day 1] 사용자가 입력하는 데이터 모델
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
    return {"message": "마이 헬스 로그 API - Day 2 가동 중"}

# [TODO 1] POST /records : 데이터 입력 시 자동 계산 및 판정 로직 추가
@app.post("/records")
def create_record(record: RecordIn):
    global current_id
    
    # 1. 입력받은 기본 데이터 가져오기
    data = record.model_dump()
    data["id"] = current_id
    
    # 2. 비만도(BMI) 계산 및 분류 로직
    # 공식: 체중(kg) / (키(m)의 제곱)
    height_m = data["height"] / 100.0  # cm 단위를 m 단위로 변환
    bmi = round(data["weight"] / (height_m ** 2), 2) if height_m > 0 else 0.0
    data["bmi"] = bmi
    
    if bmi < 18.5:
        data["bmi_status"] = "저체중"
    elif bmi < 23.0:
        data["bmi_status"] = "정상"
    elif bmi < 25.0:
        data["bmi_status"] = "과체중"
    else:
        data["bmi_status"] = "비만"
        
    # 3. 혈압 분류 로직
    sys = data["systolic"]
    dia = data["diastolic"]
    
    if sys < 120 and dia < 80:
        data["blood_pressure_status"] = "정상"
    elif sys >= 140 or dia >= 90:
        data["blood_pressure_status"] = "고혈압"
    else:
        data["blood_pressure_status"] = "전고혈압"
        
    # 4. 혈당 분류 로직
    sugar = data["blood_sugar"]
    
    if sugar < 100:
        data["blood_sugar_status"] = "정상"
    elif sugar <= 125:
        data["blood_sugar_status"] = "공복혈당장애(당뇨전단계)"
    else:
        data["blood_sugar_status"] = "당뇨"
        
    # 5. 위험 경고(Warning) 알림 조건 설정
    # 혈압이 '고혈압'이거나 혈당이 '당뇨' 단계이면 경고 발령
    if data["blood_pressure_status"] == "고혈압" or data["blood_sugar_status"] == "당뇨":
        data["warning"] = True
        data["warning_message"] = "⚠️ 고위험 수치가 감지되었습니다. 전문의와 상담을 권장합니다."
    else:
        data["warning"] = False
        data["warning_message"] = ""

    # 최종 연산 데이터 리스트에 추가 후 아이디 증가
    records.append(data)
    current_id += 1
    return data

# [TODO 2] GET /records : 전체 기록 조회
@app.get("/records")
def get_records():
    return {"total_count": len(records), "data": records}

# [TODO 3] GET /records/{record_id} : 단건 조회
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