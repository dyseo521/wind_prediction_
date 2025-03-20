"""
전력 예측 라우터 - 풍력 및 지압 발전량 예측 API 엔드포인트
- 기상청 API 최저/최고 기온 데이터 활용
- 머신러닝 모델을 통한 실시간 발전량 예측
- 위치별 풍속 특성 고려 (건물 사이 통로 효과 등)
"""
from fastapi import APIRouter, HTTPException, Query, Path, Depends, Form
from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import traceback
import pickle
import os
import json
from pydantic import BaseModel
from power_calculation import PowerCalculator
from time_series_analysis import TimeSeriesAnalyzer
import joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score

# 라우터 생성
router = APIRouter(prefix="/api/power", tags=["power"])

# 전력 계산기 인스턴스
power_calculator = PowerCalculator()

# 시계열 분석기 인스턴스
try:
    time_series_analyzer = TimeSeriesAnalyzer(model_dir=os.getenv("MODEL_DIR", "models"))
    time_series_models_loaded = time_series_analyzer.load_models()
    if not time_series_models_loaded:
        print("시계열 모델을 로드하지 못했습니다. CSV 데이터를 활용하여 모델을 학습해야 합니다.")
except Exception as e:
    print(f"시계열 분석기 초기화 오류: {e}")
    time_series_analyzer = None
    time_series_models_loaded = False

# 지원하는 위치 목록
SUPPORTED_LOCATIONS = ["5호관_60주년_사이", "인경호_앞", "하이데거숲"]

# 모델 캐시
_power_prediction_model = None

def get_power_prediction_model():
    """
    전력 예측 모델 로드 (필요시 학습)
    """
    global _power_prediction_model
    
    if _power_prediction_model is not None:
        return _power_prediction_model
    
    # 모델 파일 경로
    model_path = os.path.join(os.getenv("MODEL_DIR", "models"), "power_prediction_model.pkl")
    
    try:
        # 모델 파일이 있으면 로드
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                _power_prediction_model = pickle.load(f)
                print("기존 모델 로드 성공")
                return _power_prediction_model
    except Exception as e:
        print(f"모델 로드 오류: {e}")
    
    print("모델이 없거나 로드 실패. 새 모델 생성 중...")
    
    # 모델이 없거나 로드 실패 시 간단한 모델 생성
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.impute import SimpleImputer  # NaN 값 처리를 위한 Imputer
    from sklearn.pipeline import Pipeline  # 파이프라인 구성
    
    # 간단한 샘플 데이터로 모델 학습
    # 특성: [풍속, 기온, 습도, 시간대(0-23), 인원수, 위치 인코딩]
    X_sample = []
    y_sample_wind = []
    y_sample_piezo = []
    
    # 위치별로 다른 계수
    location_encodings = {
        "5호관_60주년_사이": [1, 0, 0],
        "인경호_앞": [0, 1, 0],
        "하이데거숲": [0, 0, 1]
    }
    
    # 샘플 데이터 생성
    for location in SUPPORTED_LOCATIONS:
        for wind_speed in [1.5, 3.0, 5.5]:
            for temp in [5, 15, 25]:
                for hour in [6, 12, 18]:
                    for crowd_level in [0.5, 1.0, 1.5]:
                        # 위치별 평균 인원수
                        base_people = power_calculator.piezo_tile_settings[location]['avg_hourly_people']
                        people_count = int(base_people * crowd_level)
                        
                        # 특성 벡터 생성
                        features = [
                            wind_speed,
                            temp,
                            60,  # 습도 (고정)
                            hour,
                            people_count
                        ]
                        features.extend(location_encodings[location])
                        
                        # 발전량 계산
                        wind_power = power_calculator.calculate_wind_power(location, wind_speed, 1)
                        piezo_power = power_calculator.calculate_piezo_power(location, people_count, 1)
                        
                        # 약간의 노이즈 추가
                        wind_noise = np.random.normal(0, wind_power * 0.05)
                        piezo_noise = np.random.normal(0, piezo_power * 0.05)
                        
                        X_sample.append(features)
                        y_sample_wind.append(wind_power + wind_noise)
                        y_sample_piezo.append(piezo_power + piezo_noise)
    
    # NaN 값을 처리하기 위한 파이프라인 생성
    # 중앙값으로 NaN 값을 채우고, 그 후 RandomForestRegressor를 적용
    wind_model = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),  # NaN 값을 중앙값으로 대체
        ('model', RandomForestRegressor(n_estimators=100, random_state=42))
    ])
    
    piezo_model = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),  # NaN 값을 중앙값으로 대체
        ('model', RandomForestRegressor(n_estimators=100, random_state=42))
    ])
    
    # 모델 학습
    try:
        print("모델 학습 시작...")
        wind_model.fit(X_sample, y_sample_wind)
        piezo_model.fit(X_sample, y_sample_piezo)
        print("모델 학습 완료!")
    except Exception as e:
        print(f"모델 학습 오류: {e}")
        traceback.print_exc()
        
        # 오류 발생 시 기본 모델 사용
        print("기본 전력 예측 모델을 생성합니다.")
        from sklearn.dummy import DummyRegressor
        
        wind_model = DummyRegressor(strategy='mean')
        piezo_model = DummyRegressor(strategy='mean')
        
        wind_model.fit(X_sample, y_sample_wind)
        piezo_model.fit(X_sample, y_sample_piezo)
    
    # 모델 저장
    _power_prediction_model = {
        "wind_model": wind_model,
        "piezo_model": piezo_model,
        "location_encodings": location_encodings,
        "feature_names": ["wind_speed", "temperature", "humidity", "hour", "people_count", "loc1", "loc2", "loc3"],
        "created_at": datetime.now().isoformat()
    }
    
    try:
        # 모델 파일 저장
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        with open(model_path, 'wb') as f:
            pickle.dump(_power_prediction_model, f)
        print(f"새 모델 저장 완료: {model_path}")
    except Exception as e:
        print(f"모델 저장 오류: {e}")
    
    return _power_prediction_model

# CSV 파일 기반 모델 학습 함수 수정 - app.py의 train_model_task

def train_model_task(
    wind_file_path: str,
    humidity_file_path: str,
    temp_file_path: str,
    rain_file_path: str,
    model_id: str,
    test_size: float = 0.2,
    alpha: float = 0.1,
    polynomial_degree: int = 2
):
    try:
        start_time = time.time()
        
        # CSV 파일 읽기
        wind_df = read_csv_with_skip(wind_file_path)
        humidity_df = read_csv_with_skip(humidity_file_path)
        temp_df = read_csv_with_skip(temp_file_path)
        rain_df = read_csv_with_skip(rain_file_path)
        
        # 데이터 병합
        merged_data = merge_data(wind_df, humidity_df, temp_df, rain_df)
        
        # NaN 체크 및 보고
        nan_counts = merged_data.isna().sum()
        print(f"NaN 값 개수: {nan_counts}")
        
        if nan_counts.sum() > 0:
            print("데이터에 NaN 값이 있습니다. 전처리를 시작합니다...")
            
            # 중요 열이 많이 비어있는 행 삭제
            critical_columns = [col for col in merged_data.columns if 'Wind' in col or 'Temp' in col]
            merged_data = merged_data.dropna(subset=critical_columns, how='all')
            
            # 나머지 NaN 값은 채우기 (Forward Fill -> Backward Fill -> Median)
            merged_data = merged_data.fillna(method='ffill').fillna(method='bfill')
            
            # 여전히 남은 NaN은 열별 중앙값으로 대체
            for col in merged_data.columns:
                if merged_data[col].isna().sum() > 0:
                    if np.issubdtype(merged_data[col].dtype, np.number):
                        merged_data[col] = merged_data[col].fillna(merged_data[col].median())
                    else:
                        merged_data[col] = merged_data[col].fillna(merged_data[col].mode()[0])
            
            print("전처리 완료. 남은 NaN 값 개수:", merged_data.isna().sum().sum())
        
        # 특성과 타겟 분리
        feature_columns = [
            'AvgHumidity_percent', 'MinHumidity_percent', 
            'AvgTemp_C', 'MaxTemp_C', 'MinTemp_C',
            'Precipitation_mm', 'MaxHourlyPrecipitation_mm'
        ]
        
        # 필요한 열이 있는지 확인하고 없으면 대체
        available_columns = []
        for col in feature_columns:
            if col in merged_data.columns:
                available_columns.append(col)
            else:
                # 비슷한 이름의 열 찾기
                for existing_col in merged_data.columns:
                    if 'Humidity' in col and 'Humidity' in existing_col:
                        available_columns.append(existing_col)
                        break
                    elif 'Temp' in col and 'Temp' in existing_col:
                        available_columns.append(existing_col)
                        break
                    elif 'Precipitation' in col and 'Precipitation' in existing_col:
                        available_columns.append(existing_col)
                        break
        
        # 타겟 열 확인
        target_column = None
        for col in merged_data.columns:
            if 'WindSpeed' in col and 'Avg' in col:
                target_column = col
                break
        
        if not target_column:
            raise ValueError("평균풍속 열을 찾을 수 없습니다.")
        
        X = merged_data[available_columns]
        y = merged_data[target_column]
        
        # 결측치 처리를 위한 파이프라인 구성
        from sklearn.impute import SimpleImputer
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import PolynomialFeatures
        
        # 1. 선형 회귀 모델 (릿지 회귀)
        linear_pipeline = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('model', Ridge(alpha=alpha))
        ])
        linear_pipeline.fit(X, y)
        
        # 2. 다항식 특성 + 릿지 회귀 모델
        poly_pipeline = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('poly', PolynomialFeatures(degree=polynomial_degree, include_bias=False)),
            ('model', Ridge(alpha=alpha*10))
        ])
        poly_pipeline.fit(X, y)
        
        # 모델 평가
        linear_pred = linear_pipeline.predict(X)
        poly_pred = poly_pipeline.predict(X)
        
        # 훈련/테스트 세트 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # 테스트 세트에서 평가
        linear_test_pred = linear_pipeline.predict(X_test)
        poly_test_pred = poly_pipeline.predict(X_test)
        
        # 평가 지표
        metrics = {
            'linear': {
                'mse': float(mean_squared_error(y_test, linear_test_pred)),
                'rmse': float(np.sqrt(mean_squared_error(y_test, linear_test_pred))),
                'mae': float(mean_absolute_error(y_test, linear_test_pred)),
                'r2': float(r2_score(y_test, linear_test_pred))
            },
            'polynomial': {
                'mse': float(mean_squared_error(y_test, poly_test_pred)),
                'rmse': float(np.sqrt(mean_squared_error(y_test, poly_test_pred))),
                'mae': float(mean_absolute_error(y_test, poly_test_pred)),
                'r2': float(r2_score(y_test, poly_test_pred))
            }
        }
        
        # 특성 이름 가져오기
        feature_names = [col.split('_')[0] for col in available_columns]
        
        # 특성 중요도 계산 (선형 모델)
        # 파이프라인에서 모델 가져오기
        linear_model = linear_pipeline.named_steps['model']
        feature_importance = [
            {"feature": name, "importance": float(abs(coef))}
            for name, coef in zip(feature_names, linear_model.coef_)
        ]
        feature_importance.sort(key=lambda x: x["importance"], reverse=True)
        
        # 계수 추출
        coefficients = {
            name: float(coef) for name, coef in zip(feature_names, linear_model.coef_)
        }
        
        # 샘플 예측
        sample_index = np.random.choice(len(X_test), min(5, len(X_test)), replace=False)
        sample_predictions = []
        for idx in sample_index:
            actual = float(y_test.iloc[idx])
            linear_predicted = float(linear_test_pred[idx])
            poly_predicted = float(poly_test_pred[idx])
            sample_predictions.append({
                "actual": actual,
                "linear_predicted": linear_predicted,
                "poly_predicted": poly_predicted,
                "linear_diff": abs(actual - linear_predicted),
                "poly_diff": abs(actual - poly_predicted)
            })
        
        # 모델 저장
        model_data = {
            "linear_pipeline": linear_pipeline,
            "poly_pipeline": poly_pipeline,
            "feature_names": feature_names,
            "coefficients": coefficients,
            "metrics": metrics,
            "feature_importance": feature_importance,
            "created_at": datetime.now().isoformat(),
            "model_id": model_id
        }
        
        model_path = os.path.join(MODEL_DIR, f"{model_id}.pkl")
        joblib.dump(model_data, model_path)
        
        # 훈련 시간 계산
        training_time = time.time() - start_time
        
        # 결과 캐싱
        training_result = {
            "model_id": model_id,
            "metrics": metrics,
            "feature_importance": feature_importance,
            "training_time": training_time,
            "sample_predictions": sample_predictions,
            "status": "completed"
        }
        
        cache_path = os.path.join(CACHE_DIR, f"training_{model_id}.json")
        with open(cache_path, 'w') as f:
            import json
            json.dump(training_result, f)
        
        return training_result
    except Exception as e:
        print(f"모델 훈련 오류: {e}")
        traceback.print_exc()
        
        # 오류 기록
        error_result = {
            "model_id": model_id,
            "status": "failed",
            "error": str(e)
        }
        
        cache_path = os.path.join(CACHE_DIR, f"training_{model_id}.json")
        with open(cache_path, 'w') as f:
            import json
            json.dump(error_result, f)
        
        return error_result

def create_default_power_model():
    """기본 전력 예측 모델 생성"""
    print("기본 전력 예측 모델을 생성합니다.")
    
    # 기본 데이터 생성
    np.random.seed(42)
    n_samples = 500
    
    # 샘플 데이터 생성
    X_sample = []
    y_wind_sample = []
    y_piezo_sample = []
    
    # 각 위치별로 샘플 생성
    for location in SUPPORTED_LOCATIONS:
        wind_factor = power_calculator.wind_turbine_settings[location]['wind_factor']
        avg_people = power_calculator.piezo_tile_settings[location]['avg_hourly_people']
        
        # 다양한 조건에서 샘플 생성
        for _ in range(n_samples // len(SUPPORTED_LOCATIONS)):
            # 임의의 환경 조건
            wind_speed = np.random.uniform(0.5, 10.0)
            temp = np.random.uniform(-5, 35)
            temp_range = np.random.uniform(2, 20)
            min_temp = temp - temp_range/2
            max_temp = temp + temp_range/2
            humidity = np.random.uniform(30, 90)
            rainfall = np.random.exponential(0.5) if np.random.random() < 0.3 else 0
            hour = np.random.randint(0, 24)
            
            # 날씨 정보
            temp_info = {
                'current': temp,
                'min': min_temp,
                'max': max_temp
            }
            
            # 전력 계산
            result = power_calculator.calculate_total_power(
                location, wind_speed, None, 1, temp_info
            )
            
            # 특성 벡터 생성
            features = [
                wind_speed,               # 풍속
                wind_speed * 1.2,         # 최대 풍속
                temp,                     # 평균 기온
                max_temp,                 # 최고 기온
                min_temp,                 # 최저 기온
                temp_range,               # 기온 범위
                humidity,                 # 평균 습도
                humidity * 0.9,           # 최저 습도
                rainfall,                 # 강수량
                rainfall * 0.8,           # 최대시간강수량
                hour,                     # 시간
                hour // 4,                # 시간대
                np.random.randint(1, 13), # 월
                wind_factor,              # 풍속 가중치
                temp_range,               # 기온 범위
                1 if location == '5호관_60주년_사이' else 0,
                1 if location == '인경호_앞' else 0,
                1 if location == '하이데거숲' else 0
            ]
            
            X_sample.append(features)
            y_wind_sample.append(result['wind_power_wh'])
            y_piezo_sample.append(result['piezo_power_wh'])
    
    # 특성 이름
    feature_names = [
        'AvgWindSpeed_mps', 'MaxWindSpeed_mps',
        'AvgTemp_C', 'MaxTemp_C', 'MinTemp_C', 'DailyTempRange_C',
        'AvgHumidity_percent', 'MinHumidity_percent',
        'Precipitation_mm', 'MaxHourlyPrecipitation_mm',
        'Hour', 'TimeBlock', 'Month',
        'wind_factor', 'temp_range',
        'location_5호관_60주년_사이', 'location_인경호_앞', 'location_하이데거숲'
    ]
    
    # 모델 학습
    wind_model = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', GradientBoostingRegressor(n_estimators=100, random_state=42))
    ])
    wind_model.fit(X_sample, y_wind_sample)
    
    piezo_model = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ])
    piezo_model.fit(X_sample, y_piezo_sample)
    
    # 특성 중요도
    wind_importance = wind_model.named_steps['regressor'].feature_importances_
    wind_feature_importance = dict(zip(feature_names, wind_importance))
    
    piezo_importance = piezo_model.named_steps['regressor'].feature_importances_
    piezo_feature_importance = dict(zip(feature_names, piezo_importance))
    
    return {
        "wind_model": wind_model,
        "piezo_model": piezo_model,
        "features": feature_names,
        "wind_feature_importance": wind_feature_importance,
        "piezo_feature_importance": piezo_feature_importance,
        "created_at": datetime.now().isoformat()
    }

# 요청/응답 모델
class PowerPredictionRequest(BaseModel):
    location: str
    wind_speed: float
    temperature: float = 20.0
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    humidity: float = 60.0
    hour: Optional[int] = None  # 현재 시간으로 설정
    people_count: Optional[int] = None  # 위치별 기본값 사용

class PowerPredictionResponse(BaseModel):
    location: str
    wind_power_wh: float
    piezo_power_wh: float
    total_power_wh: float
    streetlight_consumption_wh: float
    power_balance_wh: float
    is_sufficient: bool
    sufficiency_percentage: float
    prediction_time: str
    temperature_info: Optional[Dict[str, Any]] = None
    model_info: Optional[Dict[str, Any]] = None

@router.get("/")
async def get_power_info():
    """
    전력 예측 API 정보 조회
    """
    return {
        "name": "전력 예측 API",
        "version": "2.0.0",
        "features": [
            "기상청 API 최저/최고 기온 데이터 활용",
            "머신러닝 모델을 통한 발전량 예측",
            "위치별 풍속 특성 고려 (건물 사이 통로 효과 등)",
            "시계열 분석 지원 (CSV 데이터 기반)"
        ],
        "supported_locations": SUPPORTED_LOCATIONS,
        "endpoints": [
            {"path": "/api/power/predict", "method": "POST", "description": "시간당 발전량 예측"},
            {"path": "/api/power/ml-predict", "method": "POST", "description": "머신러닝 기반 발전량 예측"},
            {"path": "/api/power/realtime/{location}", "method": "GET", "description": "기상청 API 기반 실시간 발전량 예측"},
            {"path": "/api/power/daily/{location}", "method": "GET", "description": "일일 발전량 예측"},
            {"path": "/api/power/weekly/{location}", "method": "GET", "description": "주간 발전량 예측"},
            {"path": "/api/power/monthly/{location}", "method": "GET", "description": "월간 발전량 예측"},
            {"path": "/api/power/annual/{location}", "method": "GET", "description": "연간 발전량 예측"}
        ]
    }

@router.post("/predict", response_model=PowerPredictionResponse)
async def predict_power(request: PowerPredictionRequest):
    """
    시간당 전력 발전량 예측
    """
    try:
        # 위치 유효성 검사
        if request.location not in SUPPORTED_LOCATIONS:
            raise HTTPException(status_code=400, detail=f"지원되지 않는 위치: {request.location}. 지원되는 위치: {SUPPORTED_LOCATIONS}")
        
        # 시간 설정 (None인 경우 현재 시간 사용)
        hour = request.hour if request.hour is not None else datetime.now().hour
        
        # 온도 정보 설정
        temp_info = None
        if request.min_temperature is not None and request.max_temperature is not None:
            temp_info = {
                'current': request.temperature,
                'min': request.min_temperature,
                'max': request.max_temperature
            }
        
        # 발전량 계산
        result = power_calculator.calculate_total_power(
            request.location,
            request.wind_speed,
            request.people_count,
            1,  # 1시간
            temp_info
        )
        
        # 응답 생성
        response = PowerPredictionResponse(
            location=request.location,
            wind_power_wh=result['wind_power_wh'],
            piezo_power_wh=result['piezo_power_wh'],
            total_power_wh=result['total_power_wh'],
            streetlight_consumption_wh=result['streetlight_consumption_wh'],
            power_balance_wh=result['power_balance_wh'],
            is_sufficient=result['is_sufficient'],
            sufficiency_percentage=result['sufficiency_percentage'],
            prediction_time=datetime.now().isoformat(),
            temperature_info=result.get('temperature_info')
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"전력 예측 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"전력 예측 중 오류 발생: {str(e)}")

def predict_power_with_ml(location, wind_speed, temperature, humidity, hour, people_count):
    """
    머신러닝 모델을 사용한 전력 발전량 예측
    
    Args:
        location (str): 위치
        wind_speed (float): 풍속 (m/s)
        temperature (float): 기온 (°C)
        humidity (float): 습도 (%)
        hour (int): 시간 (0-23)
        people_count (int): 인원 수
        
    Returns:
        tuple: (풍력 발전량, 지압 발전량) (Wh)
    """
    try:
        # 모델 로드
        model = get_power_prediction_model()
        
        # 위치 인코딩
        location_encoding = model.get("location_encodings", {}).get(location)
        if not location_encoding:
            # 위치 인코딩이 없으면 기본값 사용
            location_encoding = [0, 0, 0]
            if location == "5호관_60주년_사이":
                location_encoding = [1, 0, 0]
            elif location == "인경호_앞":
                location_encoding = [0, 1, 0]
            elif location == "하이데거숲":
                location_encoding = [0, 0, 1]
        
        # 특성 벡터 생성
        features = [
            wind_speed,
            temperature,
            humidity,
            hour,
            people_count
        ]
        features.extend(location_encoding)
        
        # 모델 예측
        # 수정: model['features'] 대신 모델 구조 확인
        wind_model = model.get("wind_model")
        piezo_model = model.get("piezo_model")
        
        if not wind_model or not piezo_model:
            raise ValueError("모델이 올바르게 로드되지 않았습니다.")
        
        # 예측 수행
        wind_power = wind_model.predict([features])[0]
        piezo_power = piezo_model.predict([features])[0]
        
        return float(wind_power), float(piezo_power)
    
    except Exception as e:
        print(f"머신러닝 기반 전력 예측 오류: {e}")
        traceback.print_exc()
        
        # 에러 발생 시 기본 계산 방식으로 계산 - 기본값 반환
        return None, None
@router.get("/daily/{location}")
async def predict_daily_power(
    location: str = Path(..., description="위치 (5호관_60주년_사이, 인경호_앞, 하이데거숲)"),
    avg_wind_speed: float = Query(3.5, description="평균 풍속 (m/s)")
):
    """
    일일 전력 발전량 예측
    """
    try:
        # 위치 유효성 검사
        if location not in SUPPORTED_LOCATIONS:
            raise HTTPException(status_code=400, detail=f"지원되지 않는 위치: {location}. 지원되는 위치: {SUPPORTED_LOCATIONS}")
        
        # 시간별 풍속 생성 (간단한 모델)
        hourly_wind_speeds = []
        for hour in range(24):
            # 시간에 따른 풍속 변동 모델 (0-6시: -20%, 6-12시: 기준, 12-18시: +20%, 18-24시: 기준)
            if 0 <= hour < 6:
                hourly_wind_speeds.append(avg_wind_speed * 0.8)
            elif 6 <= hour < 12:
                hourly_wind_speeds.append(avg_wind_speed)
            elif 12 <= hour < 18:
                hourly_wind_speeds.append(avg_wind_speed * 1.2)
            else:
                hourly_wind_speeds.append(avg_wind_speed)
        
        # 시간별 인원 수 생성 (간단한 모델)
        avg_hourly_people = power_calculator.piezo_tile_settings[location]['avg_hourly_people']
        hourly_people_counts = []
        
        for hour in range(24):
            # 시간에 따른 인원 수 변동 모델
            if 0 <= hour < 6:  # 심야
                hourly_people_counts.append(int(avg_hourly_people * 0.1))
            elif 6 <= hour < 9:  # 아침침
                hourly_people_counts.append(int(avg_hourly_people * 1.2))
            elif 9 <= hour < 12:  # 오전
                hourly_people_counts.append(int(avg_hourly_people * 1.5))
            elif 12 <= hour < 14:  # 점심
                hourly_people_counts.append(int(avg_hourly_people * 1.8))
            elif 14 <= hour < 18:  # 오후
                hourly_people_counts.append(int(avg_hourly_people * 1.2))
            elif 18 <= hour < 21:  # 저녁
                hourly_people_counts.append(int(avg_hourly_people * 0.8))
            else:  # 야간
                hourly_people_counts.append(int(avg_hourly_people * 0.3))
        
        # 일일 발전량 예측
        result = power_calculator.predict_daily_power(location, hourly_wind_speeds, hourly_people_counts)
        
        # 시간별 결과 보강
        for i, hourly_result in enumerate(result['hourly_results']):
            hourly_result['hour'] = i
            hourly_result['formatted_hour'] = f"{i:02d}:00"
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"일일 전력 예측 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"일일 전력 예측 중 오류 발생: {str(e)}")

@router.get("/weekly/{location}")
async def predict_weekly_power(
    location: str = Path(..., description="위치 (5호관_60주년_사이, 인경호_앞, 하이데거숲)"),
    avg_wind_speed: float = Query(3.5, description="평균 풍속 (m/s)")
):
    """
    주간 전력 발전량 예측
    """
    try:
        # 위치 유효성 검사
        if location not in SUPPORTED_LOCATIONS:
            raise HTTPException(status_code=400, detail=f"지원되지 않는 위치: {location}. 지원되는 위치: {SUPPORTED_LOCATIONS}")
        
        # 일별 풍속 생성 (간단한 변동)
        daily_wind_speeds = []
        for day in range(7):
            # 요일에 따른 약간의 변동 (-10% ~ +10%)
            variation = 0.1 * np.sin(day * np.pi / 3.5)
            daily_wind_speeds.append(avg_wind_speed * (1 + variation))
        
        # 주간 발전량 예측
        result = power_calculator.predict_weekly_power(location, daily_wind_speeds)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"주간 전력 예측 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"주간 전력 예측 중 오류 발생: {str(e)}")

# 추가된 월간 발전량 예측 엔드포인트
@router.get("/monthly/{location}")
async def predict_monthly_power(
    location: str = Path(..., description="위치 (5호관_60주년_사이, 인경호_앞, 하이데거숲)"),
    avg_wind_speed: float = Query(3.5, description="평균 풍속 (m/s)"),
    min_temp: float = Query(5.0, description="최저 기온 (°C)"),
    max_temp: float = Query(25.0, description="최고 기온 (°C)")
):
    """
    월간 전력 발전량 예측
    """
    try:
        # 위치 유효성 검사
        if location not in SUPPORTED_LOCATIONS:
            raise HTTPException(status_code=400, detail=f"지원되지 않는 위치: {location}. 지원되는 위치: {SUPPORTED_LOCATIONS}")
        
        # 주별 풍속 생성 (평균 풍속에서 약간의 변동 추가)
        weekly_wind_speeds = [
            avg_wind_speed * (1 + 0.05 * (i - 1.5)) for i in range(4)  # 4주
        ]
        
        # 온도 정보 설정
        temp_info = {
            'min': min_temp,
            'max': max_temp,
            'current': (min_temp + max_temp) / 2  # 평균 기온
        }
        
        # 월간 발전량 예측
        result = power_calculator.predict_monthly_power(location, weekly_wind_speeds, None, temp_info)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"월간 전력 예측 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"월간 전력 예측 중 오류 발생: {str(e)}")

# 추가된 연간 발전량 예측 엔드포인트
@router.get("/annual/{location}")
async def predict_annual_power(
    location: str = Path(..., description="위치 (5호관_60주년_사이, 인경호_앞, 하이데거숲)")
):
    """
    연간 전력 발전량 예측
    """
    try:
        # 위치 유효성 검사
        if location not in SUPPORTED_LOCATIONS:
            raise HTTPException(status_code=400, detail=f"지원되지 않는 위치: {location}. 지원되는 위치: {SUPPORTED_LOCATIONS}")
        
        # 연간 발전량 예측
        result = power_calculator.predict_annual_power(location)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"연간 전력 예측 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"연간 전력 예측 중 오류 발생: {str(e)}")

@router.get("/realtime/{location}")
async def predict_realtime_power(
    location: str = Path(..., description="위치 (5호관_60주년_사이, 인경호_앞, 하이데거숲)"),
):
    """
    실시간 전력 발전량 예측 (기상청 API 데이터 활용)
    """
    try:
        # 위치 유효성 검사
        if location not in SUPPORTED_LOCATIONS:
            raise HTTPException(status_code=400, detail=f"지원되지 않는 위치: {location}. 지원되는 위치: {SUPPORTED_LOCATIONS}")
        
        # 기상청 API 데이터 가져오기 (별도의 모듈에서 구현 필요)
        try:
            from weather_router import get_current_weather
            weather_data = await get_current_weather()
            
            # 현재 풍속
            wind_speed = weather_data.get('weather', {}).get('windSpeed', 3.0)
            
            # 현재 기온
            temperature = weather_data.get('weather', {}).get('temperature', 20.0)
            
            # 현재 습도
            humidity = weather_data.get('weather', {}).get('humidity', 60.0)
            
            # 현재 시간
            current_hour = datetime.now().hour
            
            # 시간에 따른 인원 수 조정
            avg_hourly_people = power_calculator.piezo_tile_settings[location]['avg_hourly_people']
            if 0 <= current_hour < 6:  # 심야
                people_count = int(avg_hourly_people * 0.1)
            elif 6 <= current_hour < 9:  # 출근 시간
                people_count = int(avg_hourly_people * 1.2)
            elif 9 <= current_hour < 12:  # 오전
                people_count = int(avg_hourly_people * 1.5)
            elif 12 <= current_hour < 14:  # 점심
                people_count = int(avg_hourly_people * 1.8)
            elif 14 <= current_hour < 18:  # 오후
                people_count = int(avg_hourly_people * 1.2)
            elif 18 <= current_hour < 21:  # 저녁
                people_count = int(avg_hourly_people * 0.8)
            else:  # 야간
                people_count = int(avg_hourly_people * 0.3)
            
            # 머신러닝 기반 예측 시도
            try:
                # 여기에서 predict_power_with_ml 함수를 수정된 인자로 호출
                ml_wind_power, ml_piezo_power = predict_power_with_ml(
                    location=location, 
                    wind_speed=wind_speed, 
                    temperature=temperature, 
                    humidity=humidity, 
                    hour=current_hour, 
                    people_count=people_count
                )
                
                if ml_wind_power is not None and ml_piezo_power is not None:
                    # 머신러닝 결과가 있으면 기본 계산과 함께 앙상블
                    # 기본 계산
                    base_result = power_calculator.calculate_total_power(location, wind_speed, people_count, 1)
                    
                    # 앙상블 (70% 기본 계산 + 30% ML)
                    result = base_result.copy()
                    result['wind_power_wh'] = round(base_result['wind_power_wh'] * 0.7 + ml_wind_power * 0.3, 2)
                    result['piezo_power_wh'] = round(base_result['piezo_power_wh'] * 0.7 + ml_piezo_power * 0.3, 2)
                    result['total_power_wh'] = result['wind_power_wh'] + result['piezo_power_wh']
                    result['power_balance_wh'] = result['total_power_wh'] - result['streetlight_consumption_wh']
                    result['is_sufficient'] = result['power_balance_wh'] >= 0
                    result['sufficiency_percentage'] = round((result['total_power_wh'] / max(0.1, result['streetlight_consumption_wh'])) * 100, 1)
                else:
                    # ML 예측 실패 시 기본 방식 사용
                    print("머신러닝 예측 오류 (기본 방식으로 대체): ML 예측값이 None입니다")
                    result = power_calculator.calculate_total_power(location, wind_speed, people_count, 1)
            except Exception as e:
                # ML 예측 실패 시 기본 방식으로 발전량 계산
                print(f"머신러닝 예측 오류 (기본 방식으로 대체): {e}")
                result = power_calculator.calculate_total_power(location, wind_speed, people_count, 1)
            
            # 날씨 정보 추가
            result['weather'] = weather_data.get('weather', {})
            result['current_hour'] = current_hour
            result['prediction_time'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            # 기상청 API 호출 실패 시 기본값 사용
            print(f"기상청 API 호출 오류: {e}")
            traceback.print_exc()
            
            # 기본 풍속 및 시간 설정
            wind_speed = 3.0
            current_hour = datetime.now().hour
            
            # 시간에 따른 인원 수 조정
            avg_hourly_people = power_calculator.piezo_tile_settings[location]['avg_hourly_people']
            if 0 <= current_hour < 6:  # 심야
                people_count = int(avg_hourly_people * 0.1)
            elif 6 <= current_hour < 9:  # 출근 시간
                people_count = int(avg_hourly_people * 1.5)
            elif 9 <= current_hour < 12:  # 오전
                people_count = int(avg_hourly_people * 1.2)
            elif 12 <= current_hour < 14:  # 점심
                people_count = int(avg_hourly_people * 1.8)
            elif 14 <= current_hour < 18:  # 오후
                people_count = int(avg_hourly_people * 1.2)
            elif 18 <= current_hour < 21:  # 저녁
                people_count = int(avg_hourly_people * 0.8)
            else:  # 야간
                people_count = int(avg_hourly_people * 0.3)
            
            # 발전량 계산
            result = power_calculator.calculate_total_power(location, wind_speed, people_count, 1)
            
            # 기본 날씨 정보 추가
            result['weather'] = {
                'temperature': 20,
                'humidity': 60,
                'windSpeed': wind_speed
            }
            result['current_hour'] = current_hour
            result['prediction_time'] = datetime.now().isoformat()
            result['api_error'] = str(e)
            
            return result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"실시간 전력 예측 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"실시간 전력 예측 중 오류 발생: {str(e)}")