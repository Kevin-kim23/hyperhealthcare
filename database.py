import sqlite3
import os

DB_FILE = "health_log.db"

# [SQL 연결 함수] DB 파일과 소통하는 가드레일을 엽니다.
def get_connection():
    conn = sqlite3.connect(DB_FILE)
    # 데이터를 딕셔너리(Dict) 형태로 예쁘게 꺼내오도록 설정
    conn.row_factory = sqlite3.Row
    return conn

# [테이블 생성 함수] 서버 초기 구동 시 'records' 테이블이 없으면 SQL 명령어로 자동 생성합니다.
def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            weight REAL,
            height REAL,
            systolic INTEGER,
            diastolic INTEGER,
            blood_sugar INTEGER,
            steps INTEGER DEFAULT 0,
            sleep_hours REAL DEFAULT 0.0,
            memo TEXT,
            bmi REAL,
            bmi_status TEXT,
            blood_pressure_status TEXT,
            blood_sugar_status TEXT,
            warning INTEGER,
            warning_message TEXT
        )
    """)
    conn.commit()
    conn.close()

# 💡 database.py가 최초 구동될 때 자동으로 테이블 설계도를 실행합니다.
create_table()

# [SQL 저장 로직] 사용자가 입력하고 연산된 값을 SQL INSERT 쿼리문으로 영구 적재합니다.
def save_record(data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        INSERT INTO records (
            date, weight, height, systolic, diastolic, blood_sugar, steps, sleep_hours, memo,
            bmi, bmi_status, blood_pressure_status, blood_sugar_status, warning, warning_message
        ) VALUES (
            :date, :weight, :height, :systolic, :diastolic, :blood_sugar, :steps, :sleep_hours, :memo,
            :bmi, :bmi_status, :blood_pressure_status, :blood_sugar_status, :warning, :warning_message
        )
    """
    cursor.execute(query, data)
    conn.commit()
    
    # 방금 들어간 데이터의 고유 자동 증가 ID값 가져오기
    new_id = cursor.lastrowid
    conn.close()
    return new_id

# [SQL 전체 조회 로직] 테이블에 쌓인 모든 데이터를 SELECT문으로 가져옵니다.
def get_all_records():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM records ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    # sqlite3 결과를 파이썬 리스트/딕셔너리 형태로 가공해서 리턴
    return [dict(row) for row in rows]

# [SQL 단건 조회 로직] WHERE 조건절을 이용해 특정 ID만 골라 뽑아냅니다.
def get_record_by_id(record_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM records WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# [SQL 삭제 로직] DELETE 쿼리문으로 하드디스크 DB에서 깔끔하게 날려버립니다.
def delete_record_by_id(record_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM records WHERE id = ?", (record_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return True