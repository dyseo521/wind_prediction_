#!/usr/bin/env python
"""
시계열 모델 생성 스크립트

이 스크립트는 TimeSeriesAnalyzer를 사용하여 풍속, 기온, 습도 데이터를 
기반으로 시계열 예측 모델을 학습하고 저장합니다.
"""
import os
import sys
import time
from datetime import datetime
from time_series_analysis import TimeSeriesAnalyzer

def create_time_series_models(data_dir, model_dir):
    """시계열 모델 생성 함수"""
    print(f"[{datetime.now()}] 시계열 모델 생성 시작")
    
    # TimeSeriesAnalyzer 인스턴스 생성
    ts_analyzer = TimeSeriesAnalyzer(model_dir=model_dir)
    
    # 데이터 파일 경로 설정
    file_paths = {
        'wind': os.path.join(data_dir, 'wind_data.csv'),
        'temp': os.path.join(data_dir, 'temp_data.csv'),
        'humidity': os.path.join(data_dir, 'humidity_data.csv'),
        'rain': os.path.join(data_dir, 'rain_data.csv')
    }
    
    # 파일 존재 여부 확인
    for data_type, file_path in file_paths.items():
        if not os.path.exists(file_path):
            print(f"[오류] {data_type} 데이터 파일을 찾을 수 없습니다: {file_path}")
            print(f"샘플 데이터 파일이 없으면 모델을 학습할 수 없습니다.")
            return False
    
    try:
        # 시계열 모델 학습
        print(f"[{datetime.now()}] 모델 학습 시작")
        start_time = time.time()
        
        models = ts_analyzer.train_models(file_paths)
        
        elapsed_time = time.time() - start_time
        print(f"[{datetime.now()}] 모델 학습 완료 (소요 시간: {elapsed_time:.2f}초)")
        
        # 모델 정보 출력
        for target_column, model_info in models.items():
            metrics = model_info.get('metrics', {})
            rf_metrics = metrics.get('random_forest', {})
            ridge_metrics = metrics.get('ridge', {})
            
            print(f"\n대상 변수: {target_column}")
            print(f"  Random Forest - RMSE: {rf_metrics.get('rmse', 'N/A'):.3f}, R²: {rf_metrics.get('r2', 'N/A'):.3f}")
            print(f"  Ridge - RMSE: {ridge_metrics.get('rmse', 'N/A'):.3f}, R²: {ridge_metrics.get('r2', 'N/A'):.3f}")
        
        return True
        
    except Exception as e:
        print(f"[오류] 모델 학습 중 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # 환경 변수 또는 기본값 사용
    data_dir = os.getenv("DATA_DIR", "../data")
    model_dir = os.getenv("MODEL_DIR", "../models")
    
    # 필요한 디렉토리 생성
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)
    
    # 모델 생성
    success = create_time_series_models(data_dir, model_dir)
    
    if success:
        print("\n시계열 모델이 성공적으로 생성되었습니다.")
        print(f"모델 저장 경로: {os.path.join(model_dir, 'time_series_models.pkl')}")
    else:
        print("\n시계열 모델 생성에 실패했습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main()