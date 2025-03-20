FROM python:3.10-slim

WORKDIR /app

# 환경변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000
ENV UPLOAD_DIR=/app/uploads
ENV MODEL_DIR=/app/models
ENV CACHE_DIR=/app/cache
ENV DATA_DIR=/app/data

# 필요한 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 필요한 디렉토리 생성
RUN mkdir -p /app/uploads /app/models /app/cache /app/data /app/logs

# 백엔드 코드 복사 (현재 디렉토리의 모든 파일)
COPY . /app/

# 의존성 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 로깅 설정
ENV PYTHONPATH=/app
ENV LOG_LEVEL=DEBUG

# 시작 스크립트 작성
RUN echo '#!/bin/bash\n\
# 시스템 초기화 실행\n\
python initialize_system.py\n\
# API 서버 실행\n\
exec uvicorn app:app --host 0.0.0.0 --port 8000 --log-level debug\n\
' > /app/start.sh && chmod +x /app/start.sh

# 서버 실행 (초기화 스크립트 실행 후 서버 시작)
CMD ["/app/start.sh"]