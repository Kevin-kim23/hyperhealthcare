# 1. 파이썬 가벼운 버전으로 베이스 이미지 시작
FROM python:3.11-slim

# 2. 컨테이너 내부 작업 폴더 설정
WORKDIR /app

# 3. 필수 패키지 설치를 위해 요구사항 복사 및 설치
RUN pip install --no-cache-dir fastapi uvicorn jinja2

# 4. 내 컴퓨터의 모든 소스코드(main, database, templates 등)를 컨테이너로 복사
COPY . .

# 5. 전 세계에 오픈할 포트 개방 (FastAPI 기본 포트 8000)
EXPOSE 8000

# 6. 컨테이너가 켜질 때 자동으로 실행될 서버 구동 명령어
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]