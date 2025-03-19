from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import traceback
from datetime import datetime
from dotenv import load_dotenv
import weather_router
import power_router

# 환경변수 로드
load_dotenv()

# 파일 경로 설정
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MODEL_DIR = os.getenv("MODEL_DIR", "models")
CACHE_DIR = os.getenv("CACHE_DIR", "cache")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# FastAPI 애플리케이션 생성
app = FastAPI(title="전력 발전량 통합 시스템", 
              description="기상 데이터를 기반으로 전력 발전량을 예측하는 API", 
              version="2.0.0")

# CORS 설정 - React 앱과 통신 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 디렉토리 생성
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# 건강 확인 API
@app.get("/api/health/")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "environment": {
            "upload_dir": UPLOAD_DIR,
            "model_dir": MODEL_DIR,
            "cache_dir": CACHE_DIR
        }
    }

# 라우터 등록
try:
    # 전력 계산 모듈 및 라우터 로드
    from power_calculation import PowerCalculator
    
    # 라우터 등록
    app.include_router(power_router.router)
    app.include_router(weather_router.router)
    
    print("전력 계산 모듈 로드 완료")
except Exception as e:
    print(f"추가 모듈 로드 오류: {e}")
    traceback.print_exc()

# 메인 실행 블록
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)