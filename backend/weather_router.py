"""
기상청 API 데이터 활용 모듈
- 단기예보에서 최저/최고 기온(TMN/TMX) 정보 활용
- 초단기예보 및 실황에서 현재 기온(T1H) 정보 활용
"""
import os
import requests
import json
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse
import traceback
import time
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from zoneinfo import ZoneInfo

# 환경변수 로드
load_dotenv()

# 라우터 설정
router = APIRouter(prefix="/api/weather", tags=["weather"])

# 기상청 API 설정
KMA_API_URL = os.getenv("KMA_API_URL", "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0")
SERVICE_KEY = os.getenv("KMA_SERVICE_KEY", "")
NX = int(os.getenv("FORECAST_NX", "54"))  # 인천광역시 미추홀구 용현1.4동 X 좌표
NY = int(os.getenv("FORECAST_NY", "124"))  # 인천광역시 미추홀구 용현1.4동 Y 좌표

# 캐시 설정
current_weather_cache = None
forecast_cache = None
cache_timestamp = None
CACHE_TTL = 1800  # 30분 (초 단위)

def get_korea_time():
    return datetime.now(ZoneInfo("Asia/Seoul"))

def cache_is_valid():
    """캐시 유효성 검사"""
    global cache_timestamp
    if cache_timestamp is None:
        return False
    elapsed = time.time() - cache_timestamp
    return elapsed < CACHE_TTL

def update_cache():
    """캐시 시간 업데이트"""
    global cache_timestamp
    cache_timestamp = time.time()

def fix_service_key_encoding(service_key):
    """API 키 인코딩 문제 해결"""
    return service_key.replace('+', '%2B')

def handle_api_response(response):
    """API 응답 처리 (JSON 또는 XML)"""
    try:
        # JSON 파싱 시도
        data = response.json()
        return data, 'json'
    except json.JSONDecodeError:
        # XML 파싱 시도
        try:
            if response.text.strip().startswith('<'):
                root = ET.fromstring(response.text)
                
                # 오류 확인
                error_node = root.find('.//returnAuthMsg')
                if error_node is not None and 'SERVICE_KEY' in error_node.text:
                    reason_code = root.find('.//returnReasonCode')
                    reason_code_value = reason_code.text if reason_code is not None else 'UNKNOWN'
                    
                    print(f"[API] SERVICE KEY ERROR: {error_node.text} (Code: {reason_code_value})")
                    
                    return {
                        'response': {
                            'header': {
                                'resultCode': reason_code_value,
                                'resultMsg': error_node.text
                            }
                        }
                    }, 'xml'
                
                # 데이터 추출
                items = root.findall('.//item')
                if items:
                    xml_data = {
                        'response': {
                            'header': {
                                'resultCode': '00',
                                'resultMsg': 'NORMAL_SERVICE'
                            },
                            'body': {
                                'items': {
                                    'item': []
                                }
                            }
                        }
                    }
                    
                    for item in items:
                        item_data = {}
                        for child in item:
                            item_data[child.tag] = child.text
                        xml_data['response']['body']['items']['item'].append(item_data)
                    
                    return xml_data, 'xml'
                else:
                    return {
                        'response': {
                            'header': {
                                'resultCode': 'ERR',
                                'resultMsg': 'UNKNOWN_ERROR'
                            }
                        }
                    }, 'xml'
            else:
                return {
                    'response': {
                        'header': {
                            'resultCode': 'ERR',
                            'resultMsg': 'INVALID_RESPONSE_FORMAT'
                        }
                    }
                }, 'unknown'
        except Exception as e:
            return {
                'response': {
                    'header': {
                        'resultCode': 'ERR',
                        'resultMsg': f'PARSING_ERROR: {str(e)}'
                    }
                }
            }, 'error'

@router.get("/current")
async def get_current_weather():
    """
    현재 날씨 조회 (초단기실황)
    - 기온(T1H), 강수량(RN1), 습도(REH), 풍속(WSD), 풍향(VEC) 등 정보 제공
    """
    global current_weather_cache
    
    try:
        # 캐시가 유효하면 반환
        if current_weather_cache is not None and cache_is_valid():
            print("[Current Weather] Using valid cache")
            return current_weather_cache
        
        # 한국 시간으로 설정
        now = get_korea_time()
        base_date = now.strftime("%Y%m%d")
        
        # 매시각 40분 이전이면 이전 시각의 발표 데이터 사용
        if now.minute < 40:
             now = now - timedelta(hours=1) # 한시간 이전
             base_date = now.strftime("%Y%m%d")
             base_time = now.strftime("%H00")
        else:
             base_date = now.strftime("%Y%m%d")
             base_time = now.strftime("%H00")
        
        print(f"[Current Weather] Request for base_date: {base_date}, base_time: {base_time}")
        
        # API 키 확인
        fixed_service_key = fix_service_key_encoding(SERVICE_KEY)
        if not fixed_service_key:
            print("[Current Weather] ERROR: SERVICE_KEY is empty!")
            return FALLBACK_WEATHER
        
        # 초단기실황조회 API 호출
        url = f"{KMA_API_URL}/getUltraSrtNcst"
        params = {
            'serviceKey': urllib.parse.unquote(fixed_service_key),
            'numOfRows': 10,
            'pageNo': 1,
            'dataType': 'JSON',
            'base_date': base_date,
            'base_time': base_time,
            'nx': NX,
            'ny': NY
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        # 응답 처리
        if response.status_code != 200:
            print(f"[Current Weather] API Error: Status code {response.status_code}")
            raise Exception(f"기상청 API 응답 오류 (상태 코드: {response.status_code})")
        
        data, response_type = handle_api_response(response)
        
        # 결과 코드 확인
        result_code = data.get('response', {}).get('header', {}).get('resultCode', '')
        result_msg = data.get('response', {}).get('header', {}).get('resultMsg', '알 수 없는 오류')
        
        if result_code != '00':
            print(f"[Current Weather] API Result Error: {result_code} - {result_msg}")
            raise Exception(f"기상청 API 오류: {result_msg}")
        
        # 데이터 추출
        items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
        if not items:
            print("[Current Weather] No items found in response")
            raise Exception("기상청 API에서 데이터를 찾을 수 없습니다.")
        
        # 결과 가공
        result = {
            'location': '인천광역시 미추홀구 용현1.4동',
            'date': base_date,
            'time': base_time,
            'weather': {}
        }
        
        # 데이터 매핑
        for item in items:
            category = item.get('category')
            value = item.get('obsrValue')
            
            if not category or not value:
                continue
            
            try:
                # 기상청 API 코드값 매핑
                if category == 'T1H':  # 기온
                    result['weather']['temperature'] = float(value)
                elif category == 'RN1':  # 1시간 강수량
                    result['weather']['rainfall'] = float(value)
                elif category == 'REH':  # 습도
                    result['weather']['humidity'] = float(value)
                elif category == 'WSD':  # 풍속
                    result['weather']['windSpeed'] = float(value)
                elif category == 'VEC':  # 풍향
                    result['weather']['windDirection'] = float(value)
                elif category == 'PTY':  # 강수형태
                    precipitation_types = {
                        '0': '없음', '1': '비', '2': '비/눈', '3': '눈',
                        '5': '빗방울', '6': '빗방울눈날림', '7': '눈날림'
                    }
                    result['weather']['precipitationType'] = precipitation_types.get(value, '알 수 없음')
            except ValueError as e:
                print(f"[Current Weather] Value conversion error for {category}: {e}")
        
        # 캐시 업데이트
        current_weather_cache = result
        update_cache()
        
        return result
    
    except Exception as e:
        print(f"[Current Weather] Error: {e}")
        traceback.print_exc()
        
        # 캐시가 있으면 사용
        if current_weather_cache is not None and cache_is_valid():
            print("[Current Weather] Using cached data due to error")
            return current_weather_cache
        
        # 캐시가 없으면 기본값 반환
        print("[Current Weather] Using fallback data due to error")
        return {
            'location': '인천광역시 미추홀구 용현1.4동',
            'date': datetime.now().strftime("%Y%m%d"),
            'time': datetime.now().strftime("%H00"),
            'weather': {
                'temperature': 22.0,
                'humidity': 60.0,
                'rainfall': 0.0,
                'windSpeed': 2.5,
                'precipitationType': '없음',
                'error': str(e)
            }
        }

@router.get("/forecast/short")
async def get_short_forecast():
    """
    단기예보 조회 (향후 3일)
    - 기온(TMP), 최저/최고기온(TMN/TMX), 강수확률(POP), 강수량(PCP), 습도(REH), 풍속(WSD) 등 정보 제공
    """
    global forecast_cache
    
    try:
        # 캐시가 유효하면 반환
        if forecast_cache is not None and cache_is_valid():
            print("[Short Forecast] Using valid cache")
            return forecast_cache
        
        # 한국 시간으로 설정
        now = get_korea_time()
        base_date = now.strftime("%Y%m%d")
        
        # 발표시각에 따른 base_time 설정 (0200, 0500, 0800, 1100, 1400, 1700, 2000, 2300)
        hour = now.hour
        if hour < 2:
            base_time = "2300"
            base_date = (now - timedelta(days=1)).strftime("%Y%m%d")
        elif hour < 5:
            base_time = "0200"
        elif hour < 8:
            base_time = "0500"
        elif hour < 11:
            base_time = "0800"
        elif hour < 14:
            base_time = "1100"
        elif hour < 17:
            base_time = "1400"
        elif hour < 20:
            base_time = "1700"
        elif hour < 23:
            base_time = "2000"
        else:
            base_time = "2300"
        
        print(f"[Short Forecast] Request for base_date: {base_date}, base_time: {base_time}")
        
        # API 키 확인
        fixed_service_key = fix_service_key_encoding(SERVICE_KEY)
        if not fixed_service_key:
            print("[Short Forecast] ERROR: SERVICE_KEY is empty!")
            raise Exception("SERVICE_KEY가 설정되지 않았습니다.")
        
        # 단기예보조회 API 호출
        url = f"{KMA_API_URL}/getVilageFcst"
        params = {
            'serviceKey': urllib.parse.unquote(fixed_service_key),
            'numOfRows': 1000,  # 충분히 큰 값으로 설정
            'pageNo': 1,
            'dataType': 'JSON',
            'base_date': base_date,
            'base_time': base_time,
            'nx': NX,
            'ny': NY
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        # 응답 처리
        if response.status_code != 200:
            print(f"[Short Forecast] API Error: Status code {response.status_code}")
            raise Exception(f"기상청 API 응답 오류 (상태 코드: {response.status_code})")
        
        data, response_type = handle_api_response(response)
        
        # 결과 코드 확인
        result_code = data.get('response', {}).get('header', {}).get('resultCode', '')
        result_msg = data.get('response', {}).get('header', {}).get('resultMsg', '알 수 없는 오류')
        
        if result_code != '00':
            print(f"[Short Forecast] API Result Error: {result_code} - {result_msg}")
            raise Exception(f"기상청 API 오류: {result_msg}")
        
        # 데이터 추출
        items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
        if not items:
            print("[Short Forecast] No items found in response")
            raise Exception("기상청 API에서 데이터를 찾을 수 없습니다.")
        
        # 결과 가공
        forecast_data = {}
        min_max_temps = {}  # 일별 최저/최고 기온 저장
        
        for item in items:
            fcst_date = item.get('fcstDate')
            fcst_time = item.get('fcstTime')
            category = item.get('category')
            value = item.get('fcstValue')
            
            if not all([fcst_date, fcst_time, category, value]):
                continue
            
            key = f"{fcst_date}-{fcst_time}"
            if key not in forecast_data:
                forecast_data[key] = {
                    'date': fcst_date,
                    'time': fcst_time,
                    'weather': {}
                }
            
            try:
                # 최저/최고 기온 처리
                if category == 'TMN':  # 일 최저기온
                    if fcst_date not in min_max_temps:
                        min_max_temps[fcst_date] = {'min': None, 'max': None}
                    min_max_temps[fcst_date]['min'] = float(value)
                elif category == 'TMX':  # 일 최고기온
                    if fcst_date not in min_max_temps:
                        min_max_temps[fcst_date] = {'min': None, 'max': None}
                    min_max_temps[fcst_date]['max'] = float(value)
                
                # 일반 날씨 데이터 처리
                if category == 'TMP':  # 1시간 기온
                    forecast_data[key]['weather']['temperature'] = float(value)
                elif category == 'REH':  # 습도
                    forecast_data[key]['weather']['humidity'] = float(value)
                elif category == 'WSD':  # 풍속
                    forecast_data[key]['weather']['windSpeed'] = float(value)
                elif category == 'POP':  # 강수확률
                    forecast_data[key]['weather']['precipitationProbability'] = int(value)
                elif category == 'PCP':  # 1시간 강수량
                    forecast_data[key]['weather']['rainfall'] = value
                elif category == 'SKY':  # 하늘상태
                    sky_conditions = {'1': '맑음', '3': '구름많음', '4': '흐림'}
                    forecast_data[key]['weather']['skyCondition'] = sky_conditions.get(value, '알 수 없음')
                elif category == 'PTY':  # 강수형태
                    precipitation_types = {'0': '없음', '1': '비', '2': '비/눈', '3': '눈', '4': '소나기'}
                    forecast_data[key]['weather']['precipitationType'] = precipitation_types.get(value, '알 수 없음')
            except ValueError as e:
                print(f"[Short Forecast] Value conversion error for {category}: {e}")
        
        # 최저/최고 기온 정보를 각 시간별 예보에 추가
        for key, forecast in forecast_data.items():
            fcst_date = forecast['date']
            if fcst_date in min_max_temps:
                if min_max_temps[fcst_date]['min'] is not None:
                    forecast['weather']['minTemperature'] = min_max_temps[fcst_date]['min']
                if min_max_temps[fcst_date]['max'] is not None:
                    forecast['weather']['maxTemperature'] = min_max_temps[fcst_date]['max']
        
        # 리스트로 변환하여 정렬
        forecasts_list = list(forecast_data.values())
        
        result = {
            'location': '인천광역시 미추홀구 용현1.4동',
            'baseDate': base_date,
            'baseTime': base_time,
            'forecasts': sorted(forecasts_list, key=lambda x: f"{x['date']}{x['time']}"),
            'daily_min_max': min_max_temps  # 최저/최고 기온 정보 추가
        }
        
        # 캐시 업데이트
        forecast_cache = result
        update_cache()
        
        return result
    
    except Exception as e:
        print(f"[Short Forecast] Error: {e}")
        traceback.print_exc()
        
        # 캐시가 있으면 사용
        if forecast_cache is not None and cache_is_valid():
            print("[Short Forecast] Using cached data due to error")
            return forecast_cache
        
        # 캐시가 없으면 기본값 반환
        return {
            'location': '인천광역시 미추홀구 용현1.4동',
            'baseDate': datetime.now().strftime("%Y%m%d"),
            'baseTime': '0800',
            'forecasts': [
                {
                    'date': datetime.now().strftime("%Y%m%d"),
                    'time': '1200',
                    'weather': {
                        'temperature': 24.0,
                        'humidity': 55.0,
                        'windSpeed': 3.0,
                        'skyCondition': '구름많음',
                        'precipitationType': '없음',
                        'precipitationProbability': 10,
                        'minTemperature': 20.0,
                        'maxTemperature': 28.0
                    }
                }
            ],
            'error': str(e)
        }

@router.get("/min-max-temperatures")
async def get_min_max_temperatures():
    """
    최저/최고 기온 조회 - 별도 엔드포인트로 제공
    - 당일을 포함한 3일간 최저/최고 기온 정보 제공
    """
    try:
        # 단기예보 데이터 활용
        forecast_data = await get_short_forecast()
        if not forecast_data or 'daily_min_max' not in forecast_data:
            raise Exception("예보 데이터가 유효하지 않습니다.")
        
        daily_min_max = forecast_data.get('daily_min_max', {})
        
        # 일자별로 정렬
        result = []
        for date in sorted(daily_min_max.keys()):
            data = daily_min_max[date]
            formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
            result.append({
                'date': formatted_date,
                'minTemperature': data['min'],
                'maxTemperature': data['max']
            })
        
        return {
            'location': '인천광역시 미추홀구 용현1.4동',
            'temperatures': result
        }
    
    except Exception as e:
        print(f"[Min Max Temperatures] Error: {e}")
        raise HTTPException(status_code=500, detail=f"최저/최고 기온 조회 오류: {str(e)}")

# 풍속 위치별 가중치 정의 (5호관 60주년 사이는 건물 사이로 더 높은 풍속)
@router.get("/wind-factors")
async def get_wind_location_factors():
    """
    위치별 풍속 가중치 조회
    - 용현1.4동 기준 대비 각 위치의 풍속 가중치 제공
    """
    factors = {
        '5호관_60주년_사이': 1.4,  # 건물 사이 통로 풍속 증가
        '인경호_앞': 0.9,         # 비교적 개방된 공간
        '하이데거숲': 0.8         # 나무가 울창한 숲으로 풍속 저하
    }
    
    # 각 위치별 설명 추가
    descriptions = {
        '5호관_60주년_사이': '건물 사이 통로 효과로 풍속 약 40% 증가',
        '인경호_앞': '비교적 개방된 공간으로 기준 풍속 대비 약 10% 감소',
        '하이데거숲': '나무가 울창한 숲으로 기준 풍속 대비 약 20% 감소'
    }
    
    result = []
    for location, factor in factors.items():
        result.append({
            'location': location,
            'factor': factor,
            'description': descriptions.get(location, '')
        })
    
    return {
        'reference_location': '인천광역시 미추홀구 용현1.4동',
        'wind_factors': result
    }

# 현재 날씨와 풍속 가중치를 결합한 위치별 풍속 정보 제공
@router.get("/location-wind-speeds")
async def get_location_wind_speeds():
    """
    위치별 풍속 정보 조회
    - 현재 기상청 API 풍속에 위치별 가중치를 적용한 결과 제공
    """
    try:
        # 현재 날씨 조회
        current_weather = await get_current_weather()
        if not current_weather or 'weather' not in current_weather:
            raise Exception("날씨 데이터가 유효하지 않습니다.")
        
        # 기상청 API 풍속
        base_wind_speed = current_weather['weather'].get('windSpeed', 0.0)
        
        # 위치별 가중치
        factors = await get_wind_location_factors()
        factor_dict = {item['location']: item['factor'] for item in factors['wind_factors']}
        
        # 위치별 풍속 계산
        result = []
        for location, factor in factor_dict.items():
            location_wind_speed = base_wind_speed * factor
            
            # 풍속 단계 결정
            wind_level = get_wind_level(location_wind_speed)
            
            result.append({
                'location': location,
                'base_wind_speed': base_wind_speed,
                'factor': factor,
                'adjusted_wind_speed': round(location_wind_speed, 2),
                'wind_level': wind_level['level'],
                'wind_description': wind_level['description']
            })
        
        return {
            'reference_time': current_weather['time'],
            'reference_location': '인천광역시 미추홀구 용현1.4동',
            'location_wind_speeds': result
        }
    
    except Exception as e:
        print(f"[Location Wind Speeds] Error: {e}")
        raise HTTPException(status_code=500, detail=f"위치별 풍속 조회 오류: {str(e)}")

def get_wind_level(speed):
    """풍속 단계 결정"""
    if speed < 0.3:
        return {"level": "고요", "description": "바람이 거의 없음"}
    elif speed < 1.6:
        return {"level": "미풍", "description": "가벼운 바람"}
    elif speed < 3.4:
        return {"level": "약풍", "description": "잎이 살랑거림"}
    elif speed < 5.5:
        return {"level": "남풍", "description": "나뭇잎과 작은 가지가 흔들림"}
    elif speed < 8.0:
        return {"level": "창풍", "description": "작은 나무가 흔들림"}
    elif speed < 10.8:
        return {"level": "질풍", "description": "큰 나뭇가지가 흔들림"}
    elif speed < 13.9:
        return {"level": "강풍", "description": "나무 전체가 흔들림"}
    elif speed < 17.2:
        return {"level": "폭풍", "description": "나뭇가지가 부러짐"}
    else:
        return {"level": "폭풍 이상", "description": "구조물 손상 가능성"}