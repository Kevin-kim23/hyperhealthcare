import sqlite3

# V2 용 새로운 데이터베이스 파일 생성
DB_NAME = "health_log_v2.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. 회원 정보 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # 2. 개인별 건강 기록 테이블 (user_id 외래키 추가)
    c.execute('''
        CREATE TABLE IF NOT EXISTS health_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT, weight REAL, height REAL,
            systolic INTEGER, diastolic INTEGER, blood_sugar INTEGER,
            bmi REAL, bmi_status TEXT, blood_pressure_status TEXT,
            blood_sugar_status TEXT, warning INTEGER, warning_message TEXT,
            steps INTEGER, sleep_hours REAL, memo TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# --- 회원 가입 & 로그인 로직 ---
def create_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True # 가입 성공
    except sqlite3.IntegrityError:
        return False # 이미 존재하는 아이디
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0] # 로그인 성공 시 user_id (고유번호) 반환
    return None

# --- 건강 기록 CRUD 로직 (user_id 연동) ---
def save_record(user_id, data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO health_logs (
            user_id, date, weight, height, systolic, diastolic, blood_sugar,
            bmi, bmi_status, blood_pressure_status, blood_sugar_status,
            warning, warning_message, steps, sleep_hours, memo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, data["date"], data["weight"], data["height"],
        data["systolic"], data["diastolic"], data["blood_sugar"],
        data.get("bmi", 0), data.get("bmi_status", ""),
        data.get("blood_pressure_status", ""), data.get("blood_sugar_status", ""),
        data.get("warning", 0), data.get("warning_message", ""),
        data.get("steps", 0), data.get("sleep_hours", 0.0), data.get("memo", "")
    ))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_records_by_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM health_logs WHERE user_id=? ORDER BY date DESC, id DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_record_by_id(user_id, record_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM health_logs WHERE id=? AND user_id=?", (record_id, user_id))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# 파일이 실행될 때 테이블이 없으면 자동 생성
init_db()