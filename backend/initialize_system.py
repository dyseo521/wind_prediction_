#!/usr/bin/env python
"""
시스템 초기화 스크립트

필요한 데이터 디렉토리 생성 및 샘플 데이터 파일을 작성하고,
시계열 모델을 학습하여 시스템을 초기화합니다.

이 스크립트는 백엔드 폴더에서 실행되지만, 상위 디렉토리의 폴더들을 사용합니다.
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from pathlib import Path
import shutil
import traceback

# 현재 경로 - 백엔드 폴더 내부 가정
BACKEND_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
# 프로젝트 루트 디렉토리 - 백엔드 폴더의 상위 디렉토리
PROJECT_ROOT = BACKEND_DIR.parent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'system_init.log', mode='a')
    ]
)
logger = logging.getLogger('system_initialization')

def create_directory_structure():
    """필요한 디렉토리 구조 생성 (백엔드 폴더 외부)"""
    directories = [
        "data",
        "models",
        "uploads",
        "cache",
        "logs"
    ]
    
    for directory in directories:
        path = PROJECT_ROOT / directory
        if not path.exists():
            logger.info(f"Creating directory: {path}")
            path.mkdir(parents=True, exist_ok=True)
        else:
            logger.info(f"Directory already exists: {path}")

def create_sample_weather_data():
    """샘플 날씨 데이터 파일 생성"""
    data_dir = PROJECT_ROOT / "data"
    if not data_dir.exists():
        logger.info(f"Creating data directory: {data_dir}")
        data_dir.mkdir(parents=True, exist_ok=True)
    
    files = {
        "wind_data.csv": ["Date", "AvgWindSpeed_mps", "MaxWindSpeed_mps"],
        "temp_data.csv": ["Date", "AvgTemp_C", "MaxTemp_C", "MinTemp_C"],
        "humidity_data.csv": ["Date", "AvgHumidity_percent", "MinHumidity_percent"],
        "rain_data.csv": ["Date", "Precipitation_mm", "MaxHourlyPrecipitation_mm"]
    }
    
    # 파일이 존재하는지 확인하고 없으면 생성
    missing_files = []
    for filename, columns in files.items():
        file_path = data_dir / filename
        if not file_path.exists():
            missing_files.append((filename, columns))
    
    if not missing_files:
        logger.info("All weather data files already exist. Skipping sample data creation.")
        return
    
    logger.info(f"Creating {len(missing_files)} missing sample weather data files...")
    
    # 날짜 범위 생성 (최근 1년, 일별 데이터)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    dates = pd.date_range(start_date, end_date, freq='D')
    date_strings = dates.strftime('%Y%m%d')
    
    # 풍속 데이터 생성
    if any(filename == "wind_data.csv" for filename, _ in missing_files):
        logger.info("Creating wind_data.csv")
        wind_df = pd.DataFrame({"Date": date_strings})
        # 계절성 패턴 포함 (사인파)
        season = np.sin(np.linspace(0, 2*np.pi, len(dates)))
        wind_df["AvgWindSpeed_mps"] = np.clip(3.5 + 1.5 * season + np.random.normal(0, 0.8, len(dates)), 0, 15)
        wind_df["MaxWindSpeed_mps"] = np.clip(wind_df["AvgWindSpeed_mps"] + np.random.normal(2, 0.8, len(dates)), 0, 20)
        wind_df.to_csv(data_dir / "wind_data.csv", index=False)
    
    # 온도 데이터 생성
    if any(filename == "temp_data.csv" for filename, _ in missing_files):
        logger.info("Creating temp_data.csv")
        temp_df = pd.DataFrame({"Date": date_strings})
        # 계절성 패턴 포함 (사인파)
        season = np.sin(np.linspace(0, 2*np.pi, len(dates)))
        temp_df["AvgTemp_C"] = np.clip(15 + 10 * season + np.random.normal(0, 3, len(dates)), -10, 35)
        temp_df["MaxTemp_C"] = np.clip(temp_df["AvgTemp_C"] + np.random.normal(5, 1, len(dates)), -5, 40)
        temp_df["MinTemp_C"] = np.clip(temp_df["AvgTemp_C"] - np.random.normal(5, 1, len(dates)), -15, 30)
        temp_df.to_csv(data_dir / "temp_data.csv", index=False)
    
    # 습도 데이터 생성
    if any(filename == "humidity_data.csv" for filename, _ in missing_files):
        logger.info("Creating humidity_data.csv")
        humidity_df = pd.DataFrame({"Date": date_strings})
        # 온도에 반비례하는 패턴
        if "temp_data.csv" in [f for f, _ in missing_files]:
            # 온도 데이터를 이미 생성했다면 그걸 사용
            avg_temp = temp_df["AvgTemp_C"]
        else:
            # 온도 데이터가 없으면 계절성 패턴 생성
            season = np.sin(np.linspace(0, 2*np.pi, len(dates)))
            avg_temp = 15 + 10 * season
        
        humidity_df["AvgHumidity_percent"] = np.clip(70 - 0.3 * avg_temp + np.random.normal(0, 10, len(dates)), 30, 100)
        humidity_df["MinHumidity_percent"] = np.clip(humidity_df["AvgHumidity_percent"] - np.random.normal(15, 5, len(dates)), 20, 95)
        humidity_df.to_csv(data_dir / "humidity_data.csv", index=False)
    
    # 강수량 데이터 생성
    if any(filename == "rain_data.csv" for filename, _ in missing_files):
        logger.info("Creating rain_data.csv")
        rain_df = pd.DataFrame({"Date": date_strings})
        # 대부분 0, 가끔 큰 값
        rain_prob = np.random.uniform(0, 1, len(dates)) < 0.3  # 30% 확률로 비
        rain_df["Precipitation_mm"] = np.where(rain_prob, np.random.exponential(5, len(dates)), 0)
        rain_df["MaxHourlyPrecipitation_mm"] = rain_df["Precipitation_mm"] * np.random.uniform(0.2, 0.5, len(dates))
        rain_df.to_csv(data_dir / "rain_data.csv", index=False)
    
    logger.info("Sample weather data files created successfully.")

def train_time_series_models():
    """시계열 분석 모델 학습"""
    try:
        # 필요한 라이브러리 가져오기 (상대 경로 import를 처리)
        sys.path.append(str(BACKEND_DIR))
        from time_series_analysis import TimeSeriesAnalyzer
        
        logger.info("Initializing time series analyzer...")
        model_dir = PROJECT_ROOT / "models"
        
        analyzer = TimeSeriesAnalyzer(model_dir=str(model_dir))
        
        model_path = model_dir / "time_series_models.pkl"
        if model_path.exists():
            logger.info("Time series model file already exists. Attempting to load...")
            success = analyzer.load_models()
            if success:
                logger.info("Time series models loaded successfully.")
                return True
            else:
                logger.warning("Failed to load existing models. Will retrain.")
        
        logger.info("Training time series models...")
        file_paths = {
            'wind': str(PROJECT_ROOT / "data/wind_data.csv"),
            'temp': str(PROJECT_ROOT / "data/temp_data.csv"),
            'humidity': str(PROJECT_ROOT / "data/humidity_data.csv"),
            'rain': str(PROJECT_ROOT / "data/rain_data.csv")
        }
        
        # 모든 파일이 존재하는지 확인
        for file_type, path in file_paths.items():
            if not os.path.exists(path):
                logger.warning(f"{file_type} data file does not exist: {path}")
        
        start_time = time.time()
        models = analyzer.train_models(file_paths)
        elapsed_time = time.time() - start_time
        
        if models:
            logger.info(f"Time series models trained successfully in {elapsed_time:.2f} seconds.")
            return True
        else:
            logger.error("Failed to train time series models.")
            return False
            
    except Exception as e:
        logger.error(f"Error while training time series models: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """메인 실행 함수"""
    logger.info("Starting system initialization...")
    
    try:
        # 로그 디렉토리 처리
        log_dir = PROJECT_ROOT / 'logs'
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # 디렉토리 구조 생성
        create_directory_structure()
        
        # 샘플 데이터 생성
        create_sample_weather_data()
        
        # 시계열 모델 학습
        success = train_time_series_models()
        
        if success:
            logger.info("System initialization completed successfully.")
            return 0
        else:
            logger.error("System initialization failed.")
            return 1
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())