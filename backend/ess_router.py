"""
에너지 저장 시스템(ESS) 라우터 - 배터리 충방전 및 관리 API 엔드포인트
- 셀 충전 및 방전 모니터링
- 시간별 ESS 운영 계획 자동 생성
- 실시간 SOC 및 전압 모니터링
"""
from fastapi import APIRouter, HTTPException, Query, Path, Depends, Form, BackgroundTasks
from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import traceback
import pickle
import os
import json
from pydantic import BaseModel
from ess_controller import ESSController
from power_calculation import PowerCalculator
from time_series_analysis import TimeSeriesAnalyzer

# 라우터 생성
router = APIRouter(prefix="/api/ess", tags=["ess"])

# ESS 컨트롤러 인스턴스
ess_controller = ESSController()

# 전력 계산기 인스턴스 (기존 시스템과 연동)
power_calculator = PowerCalculator()

# 시계열 분석기 인스턴스 (기존 시스템과 연동)
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

# 요청/응답 모델
class BatteryStatusResponse(BaseModel):
    state: str
    soc: float
    voltage: float
    pack_voltage: float
    capacity: float
    temperature: float
    cell_configuration: str
    total_cells: int
    rest_info: Optional[Dict[str, Any]] = None

class ChargingRequest(BaseModel):
    power_production: float
    location: str = "5호관_60주년_사이"

class ChargingResponse(BaseModel):
    state: str
    charge_current: float
    c_rate: float
    soc: float
    voltage: float
    power_production: float

class DischargingRequest(BaseModel):
    power_production: Optional[float] = None
    location: str = "5호관_60주년_사이"
    is_nighttime: bool = True

class DischargingResponse(BaseModel):
    state: str
    discharge_current: float
    c_rate: float
    soc: float
    voltage: float
    battery_pack_voltage: Optional[float] = None
    converted_output_voltage: Optional[float] = None

class SimulationRequest(BaseModel):
    location: str
    date: str  # YYYYMMDD 형식
    avg_wind_speed: float = 3.5
    start_hour: int = 6
    end_hour: int = 18

class ESSSimulationResponse(BaseModel):
    location: str
    date: str
    initial_soc: float
    final_soc: float
    total_power_production: float
    total_discharge_power: float
    hourly_results: List[Dict[str, Any]]
    detailed_results: Optional[List[Dict[str, Any]]] = None

@router.get("/")
async def get_ess_info():
    """
    ESS 시스템 정보 조회
    """
    return {
        "name": "에너지 저장 시스템(ESS) API",
        "version": "1.0.0",
        "features": [
            "배터리 셀 충방전 관리",
            "CC/CV 충전 및 방전 제어",
            "전력 생산량에 따른 충방전 속도 자동 조절",
            "실시간 SOC 및 전압 모니터링"
        ],
        "supported_locations": SUPPORTED_LOCATIONS,
        "endpoints": [
            {"path": "/api/ess/battery/status", "method": "GET", "description": "배터리 상태 조회"},
            {"path": "/api/ess/battery/charge", "method": "POST", "description": "배터리 충전 시작"},
            {"path": "/api/ess/battery/discharge", "method": "POST", "description": "배터리 방전 시작"},
            {"path": "/api/ess/simulate/day", "method": "POST", "description": "일간 ESS 운영 시뮬레이션"}
        ]
    }

@router.get("/battery/status", response_model=BatteryStatusResponse)
async def get_battery_status():
    """
    배터리 상태 조회
    """
    try:
        return ess_controller.get_battery_status()
    except Exception as e:
        print(f"배터리 상태 조회 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"배터리 상태 조회 중 오류 발생: {str(e)}")

@router.post("/battery/charge", response_model=ChargingResponse)
async def start_battery_charging(request: ChargingRequest):
    """
    배터리 충전 시작
    """
    try:
        # 요청 유효성 검사
        if request.location not in SUPPORTED_LOCATIONS:
            raise HTTPException(status_code=400, detail=f"지원되지 않는 위치: {request.location}. 지원되는 위치: {SUPPORTED_LOCATIONS}")
        
        # 충전 시작
        charging_result = ess_controller.start_cc_charging(request.power_production)
        
        return ChargingResponse(
            state=charging_result['state'],
            charge_current=charging_result['charge_current'],
            c_rate=charging_result['c_rate'],
            soc=charging_result['soc'],
            voltage=charging_result['voltage'],
            power_production=request.power_production
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"배터리 충전 시작 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"배터리 충전 시작 중 오류 발생: {str(e)}")

@router.post("/battery/discharge", response_model=DischargingResponse)
async def start_battery_discharging(request: DischargingRequest):
    """
    배터리 방전 시작
    """
    try:
        # 요청 유효성 검사
        if request.location not in SUPPORTED_LOCATIONS:
            raise HTTPException(status_code=400, detail=f"지원되지 않는 위치: {request.location}. 지원되는 위치: {SUPPORTED_LOCATIONS}")
        
        # 방전 시작
        discharge_result = ess_controller.start_cc_discharging(request.power_production)
        
        return DischargingResponse(
            state=discharge_result['state'],
            discharge_current=discharge_result['discharge_current'],
            c_rate=discharge_result['c_rate'],
            soc=discharge_result['soc'],
            voltage=discharge_result['voltage']
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"배터리 방전 시작 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"배터리 방전 시작 중 오류 발생: {str(e)}")

@router.post("/simulate/day", response_model=ESSSimulationResponse)
async def simulate_daily_ess_operation(request: SimulationRequest):
    """
    일간 ESS 운영 시뮬레이션
    """
    try:
        # 요청 유효성 검사
        if request.location not in SUPPORTED_LOCATIONS:
            raise HTTPException(status_code=400, detail=f"지원되지 않는 위치: {request.location}. 지원되는 위치: {SUPPORTED_LOCATIONS}")
        
        if request.start_hour >= request.end_hour:
            raise HTTPException(status_code=400, detail="주간 시작 시간은 종료 시간보다 작아야 합니다.")
        
        # 일별 전력 예측
        try:
            # 일별 발전량 계산을 위한 시간별 풍속 생성
            hourly_wind_speeds = []
            for hour in range(24):
                # 시간에 따른 풍속 변동 모델 (0-6시: -20%, 6-12시: 기준, 12-18시: +20%, 18-24시: 기준)
                if 0 <= hour < 6:
                    hourly_wind_speeds.append(request.avg_wind_speed * 0.8)
                elif 6 <= hour < 12:
                    hourly_wind_speeds.append(request.avg_wind_speed)
                elif 12 <= hour < 18:
                    hourly_wind_speeds.append(request.avg_wind_speed * 1.2)
                else:
                    hourly_wind_speeds.append(request.avg_wind_speed)
            
            # 전력 예측
            daily_power = power_calculator.predict_daily_power(request.location, hourly_wind_speeds)
        except Exception as e:
            print(f"일별 전력 예측 오류: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"일별 전력 예측 중 오류 발생: {str(e)}")
        
        # 시간별 발전량 추출
        hourly_power_data = [result['total_power_wh'] for result in daily_power['hourly_results']]
        
        # ESS 상태 초기화 (테스트용)
        ess_controller.current_soc = 0.3  # 30% 충전 상태로 시작
        ess_controller.current_voltage = ess_controller.calculate_ocv(ess_controller.current_soc)
        ess_controller.system_state = "IDLE"
        
        # 시뮬레이션 실행
        simulation_result = ess_controller.simulate_day_cycle(
            hourly_power_data, 
            start_hour=request.start_hour, 
            end_hour=request.end_hour
        )
        
        # 결과 변환
        total_power_production = sum(hourly_power_data)
        
        # 방전 전력 계산 (총 방전량)
        total_discharge_power = 0
        for cycle in ess_controller.discharge_history:
            if 'initial_soc' in cycle and 'final_soc' in cycle:
                soc_change = cycle['initial_soc'] - cycle['final_soc']
                discharge_power = soc_change * ess_controller.cell_capacity * ess_controller.cells_in_parallel / 1000 * 3.7  # Wh (대략적 계산)
                total_discharge_power += discharge_power
        
        response = ESSSimulationResponse(
            location=request.location,
            date=request.date,
            initial_soc=simulation_result['summary']['initial_soc'],
            final_soc=simulation_result['summary']['final_soc'],
            total_power_production=total_power_production,
            total_discharge_power=total_discharge_power,
            hourly_results=simulation_result['summary']['hourly_results'],
            detailed_results=simulation_result['detailed_results']
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ESS 시뮬레이션 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"ESS 시뮬레이션 중 오류 발생: {str(e)}")

@router.get("/realtime/{location}")
async def get_realtime_ess_operation(location: str = Path(..., description="위치 (5호관_60주년_사이, 인경호_앞, 하이데거숲)")):
    """
    실시간 ESS 운영 상태 조회
    """
    try:
        # 위치 유효성 검사
        if location not in SUPPORTED_LOCATIONS:
            raise HTTPException(status_code=400, detail=f"지원되지 않는 위치: {location}. 지원되는 위치: {SUPPORTED_LOCATIONS}")
        
        # 실시간 전력 예측 데이터 가져오기
        try:
            from weather_router import get_location_wind_speeds
            wind_data = await get_location_wind_speeds()
            
            # 현재 위치에 맞는 풍속 정보 찾기
            location_wind_data = None
            for item in wind_data.get('location_wind_speeds', []):
                if item.get('location') == location:
                    location_wind_data = item
                    break
            
            if not location_wind_data:
                raise Exception(f"위치 {location}의 풍속 정보를 찾을 수 없습니다.")
            
            # 현재 풍속
            wind_speed = location_wind_data.get('adjusted_wind_speed', 3.0)
            
            # 실시간 전력 생산 예측
            from power_router import predict_realtime_power
            power_data = await predict_realtime_power(location)
            
            # 현재 시간
            current_hour = datetime.now().hour
            
            # 주간/야간 판단 (6시~18시: 주간, 그 외: 야간)
            is_nighttime = current_hour < 6 or current_hour >= 18
            
            # 자동 ESS 제어
            ess_control_result = ess_controller.automatic_control(
                power_data['total_power_wh'],
                is_nighttime=is_nighttime
            )
            
            # 배터리 상태 정보
            battery_status = ess_controller.get_battery_status()
            
            # 응답 데이터 구성
            response = {
                'location': location,
                'current_time': datetime.now().isoformat(),
                'is_nighttime': is_nighttime,
                'wind_speed': wind_speed,
                'power_production': power_data['total_power_wh'],
                'ess_state': ess_control_result.get('state'),
                'battery_status': battery_status,
                'weather': power_data.get('weather', {}),
                'ess_control': ess_control_result
            }
            
            # 주간/야간에 따른 추가 정보
            if is_nighttime:
                # 야간 - 방전 정보
                if battery_status['state'] == "DISCHARGING":
                    response['streetlight_support'] = {
                        'power_required': power_data['streetlight_consumption_wh'],
                        'power_from_battery': min(battery_status['soc'] * 0.01 * battery_status['capacity'] * 3.7, power_data['streetlight_consumption_wh']),
                        'battery_contribution_percentage': min(100, (battery_status['soc'] * 0.01 * battery_status['capacity'] * 3.7 / max(0.1, power_data['streetlight_consumption_wh'])) * 100)
                    }
            else:
                # 주간 - 충전 정보
                if battery_status['state'] in ["CHARGING_CC", "CHARGING_CV"]:
                    response['charging_info'] = {
                        'current_c_rate': ess_control_result.get('c_rate', 0.1),
                        'charge_current': ess_control_result.get('charge_current', 0),
                        'estimated_full_charge_time': (100 - battery_status['soc']) / max(2, battery_status['soc'] * 0.1)  # 간단한 추정
                    }
            
            return response
            
        except Exception as e:
            print(f"실시간 ESS 운영 데이터 조회 오류: {e}")
            traceback.print_exc()
            
            # 기본 데이터 반환
            return {
                'location': location,
                'current_time': datetime.now().isoformat(),
                'is_nighttime': datetime.now().hour < 6 or datetime.now().hour >= 18,
                'battery_status': ess_controller.get_battery_status(),
                'error': str(e)
            }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"실시간 ESS 운영 상태 조회 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"실시간 ESS 운영 상태 조회 중 오류 발생: {str(e)}")

@router.get("/daily-schedule/{location}")
async def get_daily_ess_schedule(
    location: str = Path(..., description="위치 (5호관_60주년_사이, 인경호_앞, 하이데거숲)"),
    date: str = Query(None, description="날짜 (YYYYMMDD 형식, 기본값: 오늘)"),
    avg_wind_speed: float = Query(3.5, description="평균 풍속 (m/s)")
):
    """
    일간 ESS 운영 스케줄 생성
    """
    try:
        # 위치 유효성 검사
        if location not in SUPPORTED_LOCATIONS:
            raise HTTPException(status_code=400, detail=f"지원되지 않는 위치: {location}. 지원되는 위치: {SUPPORTED_LOCATIONS}")
        
        # 날짜 설정 (기본값: 오늘)
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        # 시간별 풍속 생성
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
        
        # 일간 전력 예측
        daily_power = power_calculator.predict_daily_power(location, hourly_wind_speeds)
        
        # 시간별 전력 생산 및 소비 계획
        hourly_plan = []
        
        # 총 가로등 소비 전력
        total_streetlight_consumption = daily_power['streetlight_consumption_wh']
        daily_required_battery_capacity = total_streetlight_consumption * 0.5  # 배터리가 담당할 비율 (50%)
        
        # 표준 충전 시간 (8시 ~ 16시)
        charge_start_hour = 8
        charge_end_hour = 16
        
        # 충전 가능 시간의 총 발전량 계산
        charge_period_production = 0
        for i, result in enumerate(daily_power['hourly_results']):
            hour = result['hour']  # 시간 정보는 result에서 직접 가져옴
            if charge_start_hour <= hour < charge_end_hour:
                charge_period_production += result['total_power_wh']
        
        # 표준 방전 시간 (18시 ~ 6시)
        discharge_start_hour = 18
        discharge_end_hour = 6  # 다음날
        
        # 방전 필요 시간 계산
        discharge_hours = (24 - discharge_start_hour) + discharge_end_hour
        
        # 시간별 계획 생성
        for result in daily_power['hourly_results']:
            hour = result['hour']
            
            # 기본 계획 정보
            plan = {
                'hour': hour,
                'power_production': result['total_power_wh'],
                'power_consumption': total_streetlight_consumption / 12 if (hour >= 18 or hour < 6) else 0,
                'ess_mode': 'IDLE',
                'ess_power': 0
            }
            
            # 충전 시간
            if charge_start_hour <= hour < charge_end_hour:
                plan['ess_mode'] = 'CHARGING'
                
                # 생산량이 임계값(25804.8Wh)을 초과하는지 확인
                if result['total_power_wh'] > ess_controller.threshold_power / 24:
                    plan['ess_power'] = result['total_power_wh']
                    plan['charge_c_rate'] = 0.1 * 0.1 / ((6.75e-9 * (result['total_power_wh'] - ess_controller.threshold_power / 24)) + 0.1)
                else:
                    # 표준 충전
                    plan['ess_power'] = result['total_power_wh']
                    plan['charge_c_rate'] = 0.1  # 기본 0.1C
                
            # 방전 시간
            elif hour >= discharge_start_hour or hour < discharge_end_hour:
                plan['ess_mode'] = 'DISCHARGING'
                
                # 필요 방전량 계산
                required_discharge = daily_required_battery_capacity / discharge_hours
                
                # 생산량이 임계값을 초과하는지 확인
                if result['total_power_wh'] > ess_controller.threshold_power / 24:
                    plan['ess_power'] = -required_discharge  # 음수는 방전 의미
                    plan['discharge_c_rate'] = 0.0833 * ((6.75e-9 * (result['total_power_wh'] - ess_controller.threshold_power / 24)) + 0.0833) / 0.0833
                else:
                    # 표준 방전
                    plan['ess_power'] = -required_discharge  # 음수는 방전 의미
                    plan['discharge_c_rate'] = 0.0833  # 기본 0.0833C
            
            hourly_plan.append(plan)
        
        # ESS 운영 요약
        charging_hours = charge_end_hour - charge_start_hour
        charging_capacity = charge_period_production * 0.8  # 충전 효율 80% 가정
        
        ess_summary = {
            'required_battery_capacity_wh': daily_required_battery_capacity,
            'charging_period': f"{charge_start_hour}시 ~ {charge_end_hour}시",
            'discharging_period': f"{discharge_start_hour}시 ~ {discharge_end_hour}시 (다음날)",
            'max_charging_capacity_wh': charging_capacity,
            'charge_discharge_balance': charging_capacity - daily_required_battery_capacity,
            'is_sufficient': charging_capacity >= daily_required_battery_capacity
        }
        
        return {
            'location': location,
            'date': date,
            'total_power_production_wh': daily_power['daily_total_power_wh'],
            'total_streetlight_consumption_wh': total_streetlight_consumption,
            'ess_summary': ess_summary,
            'hourly_plan': hourly_plan
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"일간 ESS 운영 스케줄 생성 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"일간 ESS 운영 스케줄 생성 중 오류 발생: {str(e)}")