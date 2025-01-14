# 베이스 이미지 설정 (Python 3.9 사용)
FROM python:3.10.5

# 필수 패키지 설치
RUN apt-get update && apt-get install -y ca-certificates

# 작업 디렉토리 설정
WORKDIR /app

# 필요 파일 복사
COPY requirements.txt requirements.txt

# 의존성 설치
RUN pip install -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

EXPOSE 5000

# Flask 애플리케이션 실행
CMD ["python", "app.py"]
# CMD ["waitress-serve", "--listen=192.168.0.23:5000", "app:app"]

# 타임존 설정
ENV TZ=Asia/Seoul

# Docker 이미지를 빌드할 때, Python 애플리케이션의 표준 출력이 버퍼링되지 않도록 설정합니다.
ENV PYTHONUNBUFFERED=1 