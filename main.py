from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import database

app = FastAPI(title="마이 헬스 로그 API", version="4.5 (인자 오류 완전 수정)")

# 절대 경로를 기반으로 templates 폴더 안의 HTML을 해석하는 엔진 장착
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# 🌐 1. 메인 루트 ( 최신 버전의 인자 가드레일에 맞추어 request를 첫 번째에 배치했습니다! )
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html")


# 📝 데이터 검증을 위한 Pydantic 규격 정의
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


# 🚀 2. [POST] 건강 일지 데이터 추가 및 SQL 테이블 저장 엔드포인트
@app.post("/records")
def create_record(record: RecordIn):
    data = record.model_dump()
    
    # [Day 2] 자동 건강 분석 판정 알고리즘 가동
    height_m = data["height"] / 100.0
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
        
    sys, dia = data["systolic"], data["diastolic"]
    if sys < 120 and dia < 80:
        data["blood_pressure_status"] = "정상"
    elif sys >= 140 or dia >= 90:
        data["blood_pressure_status"] = "고혈압"
    else:
        data["blood_pressure_status"] = "전고혈압"
        
    sugar = data["blood_sugar"]
    if sugar < 100:
        data["blood_sugar_status"] = "정상"
    elif sugar <= 125:
        data["blood_sugar_status"] = "공복혈당장애(당뇨전단계)"
    else:
        data["blood_sugar_status"] = "당뇨"
        
    if data["blood_pressure_status"] == "고혈압" or data["blood_sugar_status"] == "당뇨":
        data["warning"] = 1  
        data["warning_message"] = "⚠️ 고위험 수치가 감지되었습니다. 전문의와 상담을 권장합니다."
    else:
        data["warning"] = 0
        data["warning_message"] = ""

    # database.py의 SQL 함수 안전 호출!
    new_id = database.save_record(data)
    data["id"] = new_id
    
    data["warning"] = True if data["warning"] == 1 else False
    return data


# 📊 3. [GET] 전체 기록 조회 엔드포인트
@app.get("/records")
def get_records():
    sql_records = database.get_all_records()
    for r in sql_records:
        r["warning"] = True if r["warning"] == 1 else False
    return {"total_count": len(sql_records), "data": sql_records}


# 🔍 4. [GET] 특정 ID 단건 상세 조회 엔드포인트
@app.get("/records/{record_id}")
def get_record(record_id: int):
    res = database.get_record_by_id(record_id)
    if not res:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    res["warning"] = True if res["warning"] == 1 else False
    return res


# ❌ 5. [DELETE] 특정 건강 기록 SQL에서 삭제 엔드포인트
@app.delete("/records/{record_id}")
def delete_record(record_id: int):
    success = database.delete_record_by_id(record_id)
    if not success:
        raise HTTPException(status_code=404, detail="삭제할 기록이 없습니다.")
    return {"message": f"ID {record_id} 기록이 SQL 데이터베이스에서 영구 삭제되었습니다."}