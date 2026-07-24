from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import database

app = FastAPI(title="마이 헬스 로그 API 2.0", version="5.0 (회원제 도입)")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# --- 데이터 검증 모델 (Pydantic) ---
class UserAuth(BaseModel):
    username: str
    password: str

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

# 🌐 프론트엔드 연결 루트
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html")

# 🔐 [POST] 1. 회원가입 API
@app.post("/signup")
def signup(user: UserAuth):
    success = database.create_user(user.username, user.password)
    if not success:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")
    return {"message": "회원가입이 완료되었습니다!"}

# 🔑 [POST] 2. 로그인 API (입장권 발급)
@app.post("/login")
def login(user: UserAuth):
    user_id = database.verify_user(user.username, user.password)
    if not user_id:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 틀렸습니다.")
    # 성공 시 사용자 고유 ID를 입장권(Token)처럼 반환
    return {"access_token": str(user_id), "message": "로그인 성공!"}

# 🚀 [POST] 3. 내 건강 기록 추가 (헤더에 x-user-id 필수)
@app.post("/records")
def create_record(record: RecordIn, x_user_id: int = Header(...)):
    data = record.model_dump()
    
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
        data["warning"] = 1  
        data["warning_message"] = "⚠️ 고위험 수치가 감지되었습니다. 전문의와 상담을 권장합니다."
    else:
        data["warning"] = 0
        data["warning_message"] = ""

    # 누구의 기록인지(x_user_id) 함께 DB에 저장
    new_id = database.save_record(x_user_id, data)
    data["id"] = new_id
    data["warning"] = True if data["warning"] == 1 else False
    return data

# 📊 [GET] 4. 내 기록만 조회 (헤더에 x-user-id 필수)
@app.get("/records")
def get_records(x_user_id: int = Header(...)):
    sql_records = database.get_records_by_user(x_user_id)
    for r in sql_records:
        r["warning"] = True if r["warning"] == 1 else False
    return {"total_count": len(sql_records), "data": sql_records}

# ❌ [DELETE] 5. 내 기록 삭제 (헤더에 x-user-id 필수)
@app.delete("/records/{record_id}")
def delete_record(record_id: int, x_user_id: int = Header(...)):
    success = database.delete_record_by_id(x_user_id, record_id)
    if not success:
        raise HTTPException(status_code=404, detail="삭제할 기록이 없거나 본인 기록이 아닙니다.")
    return {"message": "기록이 성공적으로 삭제되었습니다."}