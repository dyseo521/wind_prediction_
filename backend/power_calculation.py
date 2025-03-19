"""
전력 계산 모듈 - 풍력 및 지압 발전량 계산 기능을 제공합니다.
기상청 API의 최저/최고 기온과 현재 기온을 활용하여 정확도를 높입니다.
위치별 풍속 특성(건물 사이 통로 효과 등)을 고려합니다.
"""
import math
import numpy as np
from datetime import datetime, timedelta

class PowerCalculator:
    def __init__(self):
        # 풍력 발전기 설정
        self.wind_turbine_settings = {
            '5호관_60주년_사이': {
                'model': 'Lotus-V 1kW',
                'rated_power': 1000,  # Watts
                'start_wind_speed': 1.5,  # m/s
                'area': 3.14,  # m^2 (추정 단면적)
                'efficiency': 0.35,  # 효율 (35%)
                'count': 2,  # 설치 개수
                'wind_factor': 1.4  # 건물 사이 통로 효과로 풍속 증가
            },
            '인경호_앞': {
                'model': '미니 풍력 터빈 600W',
                'rated_power': 600,  # Watts
                'start_wind_speed': 1.2,  # m/s
                'area': 2.0,  # m^2 (추정 단면적)
                'efficiency': 0.30,  # 효율 (30%)
                'count': 3,  # 설치 개수
                'wind_factor': 0.9  # 개방 공간으로 풍속 약간 감소
            },
            '하이데거숲': {
                'model': 'Lotus-V 3kW',
                'rated_power': 3000,  # Watts
                'start_wind_speed': 1.5,  # m/s
                'area': 4.5,  # m^2 (추정 단면적)
                'efficiency': 0.40,  # 효율 (40%)
                'count': 1,  # 설치 개수
                'wind_factor': 0.8  # 숲으로 풍속 감소
            }
        }
        
        # 지압 발전기 설정 (기존 값 유지)
        self.piezo_tile_settings = {
            '5호관_60주년_사이': {
                'model': 'Pavegen',
                'power_per_step': 5,  # W (한 걸음당 평균 전력)
                'tiles_count': 275,   # 설치된 타일 수
                'avg_hourly_people': 754,  # 시간당 평균 인원
                'step_per_person': 4   # 한 사람당 평균 밟는 횟수
            },
            '인경호_앞': {
                'model': 'Pavegen',
                'power_per_step': 5,  # W
                'tiles_count': 200,   # 설치된 타일 수
                'avg_hourly_people': 562,  # 시간당 평균 인원
                'step_per_person': 4   # 한 사람당 평균 밟는 횟수
            },
            '하이데거숲': {
                'model': 'Pavegen',
                'power_per_step': 5,  # W
                'tiles_count': 230,   # 설치된 타일 수
                'avg_hourly_people': 616,  # 시간당 평균 인원
                'step_per_person': 4   # 한 사람당 평균 밟는 횟수
            }
        }
        
        # AC → DC 변환 효율
        self.ac_dc_efficiency = 0.70  # 70%
        
        # LED 가로등 전력 소비
        self.led_streetlight_power = 150  # W
        self.led_streetlight_hours = 12   # 하루 작동 시간
        
        # 지역별 가로등 개수
        self.streetlight_count = {
            '5호관_60주년_사이': 8,
            '인경호_앞': 9,
            '하이데거숲': 14
        }
        
        # 온도 영향 계수 (온도별 공기 밀도 변화로 인한 풍력 발전 효율 영향)
        self.temperature_factors = {
            'very_cold': 1.12,  # -10°C 이하 (매우 추운 날씨): 공기 밀도 높음 = 효율 증가
            'cold': 1.08,       # -10°C ~ 0°C (추운 날씨): 공기 밀도 다소 높음
            'cool': 1.04,       # 0°C ~ 10°C (서늘한 날씨): 약간 효율 증가
            'mild': 1.0,        # 10°C ~ 20°C (적정 온도): 기준 효율
            'warm': 0.96,       # 20°C ~ 30°C (따뜻한 날씨): 약간 효율 감소
            'hot': 0.92,        # 30°C 이상 (더운 날씨): 공기 밀도 낮음 = 효율 감소
        }
        
        # 일교차 영향 계수 (일교차가 클수록 공기 흐름이 활발해짐)
        self.temp_range_factors = {
            'small': 1.0,       # 5°C 미만: 영향 없음
            'medium': 1.05,     # 5°C ~ 10°C: 약간 효율 증가
            'large': 1.1,       # 10°C ~ 15°C: 효율 증가
            'very_large': 1.15  # 15°C 이상: 효율 크게 증가
        }

    def calculate_wind_power(self, location, wind_speed, hours=1, temp_info=None):
        """
        풍력 발전량 계산 (기온 정보 활용 가능)
        
        Args:
            location (str): 위치명 (5호관_60주년_사이, 인경호_앞, 하이데거숲)
            wind_speed (float): 기상청 기준 풍속 (m/s)
            hours (float): 발전 시간 (시간 단위)
            temp_info (dict, optional): 기온 정보 (현재기온, 최저기온, 최고기온)
                예: {'current': 22.0, 'min': 18.0, 'max': 27.0}
            
        Returns:
            float: 발전량 (Wh)
        """
        if location not in self.wind_turbine_settings:
            raise ValueError(f"지원되지 않는 위치: {location}")
            
        settings = self.wind_turbine_settings[location]
        
        # 위치별 풍속 가중치 적용 (건물 사이 통로 효과 등)
        adjusted_wind_speed = wind_speed * settings['wind_factor']
        
        # 시동 풍속 미만인 경우 발전량 없음
        if adjusted_wind_speed < settings['start_wind_speed']:
            return 0.0
            
        # 공기 밀도 (kg/m^3) - 기본값
        air_density = 1.225
        
        # 온도 영향 계수 (기본값 = 1.0)
        temp_factor = 1.0
        temp_range_factor = 1.0
        
        # 기온 정보가 제공된 경우 온도 영향 계수 적용
        if temp_info and 'current' in temp_info:
            current_temp = temp_info['current']
            
            # 현재 온도에 따른 영향 계수
            if current_temp <= -10:
                temp_factor = self.temperature_factors['very_cold']
            elif current_temp <= 0:
                temp_factor = self.temperature_factors['cold']
            elif current_temp <= 10:
                temp_factor = self.temperature_factors['cool']
            elif current_temp <= 20:
                temp_factor = self.temperature_factors['mild']
            elif current_temp <= 30:
                temp_factor = self.temperature_factors['warm']
            else:
                temp_factor = self.temperature_factors['hot']
            
            # 최저/최고 기온 정보가 있는 경우 일교차 영향 계수 적용
            if 'min' in temp_info and 'max' in temp_info:
                temp_range = temp_info['max'] - temp_info['min']
                
                if temp_range < 5:
                    temp_range_factor = self.temp_range_factors['small']
                elif temp_range < 10:
                    temp_range_factor = self.temp_range_factors['medium']
                elif temp_range < 15:
                    temp_range_factor = self.temp_range_factors['large']
                else:
                    temp_range_factor = self.temp_range_factors['very_large']
        
        # 풍력 에너지 계산식: P = 0.5 * ρ * A * v^3 * η * t * temp_factor * temp_range_factor
        # ρ: 공기 밀도, A: 단면적, v: 풍속, η: 효율, t: 시간
        raw_power = 0.5 * air_density * settings['area'] * (adjusted_wind_speed ** 3) * settings['efficiency'] * temp_factor * temp_range_factor
        
        # 정격 출력 제한
        power = min(raw_power, settings['rated_power'])
        
        # 설치 개수 고려
        total_power = power * settings['count']
        
        # 시간을 곱해 에너지(Wh)로 변환
        energy = total_power * hours
        
        # AC → DC 변환 손실 적용 (그리드 연결 시)
        return energy * self.ac_dc_efficiency

    def calculate_piezo_power(self, location, people_count=None, hours=1):
        """
        지압 발전량 계산
        
        Args:
            location (str): 위치명 (5호관_60주년_사이, 인경호_앞, 하이데거숲)
            people_count (int, optional): 인원 수. None인 경우 위치별 평균값 사용
            hours (float): 발전 시간 (시간 단위)
            
        Returns:
            float: 발전량 (Wh)
        """
        if location not in self.piezo_tile_settings:
            raise ValueError(f"지원되지 않는 위치: {location}")
            
        settings = self.piezo_tile_settings[location]
        
        # 인원 수가 명시되지 않은 경우 위치별 평균값 사용
        if people_count is None:
            people_count = settings['avg_hourly_people'] * hours
        else:
            # 시간이 1이 아닌 경우 인원 수 조정
            if hours != 1:
                people_count = people_count * hours
        
        # 총 밟는 횟수 = 인원 수 * 한 사람당 평균 밟는 횟수
        total_steps = people_count * settings['step_per_person']
        
        # 발전량 계산: 총 밟는 횟수 * 한 걸음당 전력
        power = total_steps * settings['power_per_step']
        
        # 시간을 고려해 Wh 단위로 변환 (이미 hours를 인원 수에 반영했으므로 추가 곱셈 불필요)
        energy = power
        
        # AC → DC 변환 손실 적용
        return energy * self.ac_dc_efficiency

    def calculate_total_power(self, location, wind_speed, people_count=None, hours=1, temp_info=None):
        """
        총 발전량 계산 (풍력 + 지압)
        
        Args:
            location (str): 위치명
            wind_speed (float): 풍속 (m/s)
            people_count (int, optional): 인원 수
            hours (float): 발전 시간
            temp_info (dict, optional): 기온 정보 (현재기온, 최저기온, 최고기온)
            
        Returns:
            dict: 발전량 정보 (풍력, 지압, 총합, 가로등 소비량, 잉여/부족량)
        """
        wind_power = self.calculate_wind_power(location, wind_speed, hours, temp_info)
        piezo_power = self.calculate_piezo_power(location, people_count, hours)
        total_power = wind_power + piezo_power
        
        # 가로등 소비 전력
        streetlight_count = self.streetlight_count.get(location, 0)
        streetlight_consumption = self.led_streetlight_power * streetlight_count * min(hours, self.led_streetlight_hours)
        
        # 발전량과 소비량 차이
        power_balance = total_power - streetlight_consumption
        
        # 위치별 풍속 가중치 정보 추가
        wind_factor = self.wind_turbine_settings[location]['wind_factor']
        adjusted_wind_speed = wind_speed * wind_factor
        
        # 온도 관련 정보 처리
        temp_effect = {}
        if temp_info:
            temp_effect = {
                'current_temp': temp_info.get('current'),
                'min_temp': temp_info.get('min'),
                'max_temp': temp_info.get('max')
            }
            if 'min' in temp_info and 'max' in temp_info:
                temp_effect['temp_range'] = temp_info['max'] - temp_info['min']
        
        return {
            'location': location,
            'hours': hours,
            'wind_speed': wind_speed,
            'wind_factor': wind_factor,
            'adjusted_wind_speed': round(adjusted_wind_speed, 2),
            'people_count': people_count if people_count is not None else self.piezo_tile_settings[location]['avg_hourly_people'] * hours,
            'wind_power_wh': round(wind_power, 2),
            'piezo_power_wh': round(piezo_power, 2),
            'total_power_wh': round(total_power, 2),
            'streetlight_consumption_wh': round(streetlight_consumption, 2),
            'power_balance_wh': round(power_balance, 2),
            'is_sufficient': power_balance >= 0,
            'sufficiency_percentage': round((total_power / max(0.1, streetlight_consumption)) * 100, 1) if streetlight_consumption > 0 else float('inf'),
            'temperature_info': temp_effect
        }

    def predict_daily_power(self, location, hourly_wind_speeds, hourly_people_counts=None, temp_info=None):
        """
        일일 발전량 예측
        
        Args:
            location (str): 위치명
            hourly_wind_speeds (list): 시간별 풍속 목록 (24개 요소)
            hourly_people_counts (list, optional): 시간별 인원 수 목록 (24개 요소)
            temp_info (dict, optional): 일별 기온 정보
            
        Returns:
            dict: 일일 발전량 정보
        """
        if len(hourly_wind_speeds) != 24:
            raise ValueError("시간별 풍속은 24개 요소를 가진 목록이어야 합니다.")
            
        if hourly_people_counts is not None and len(hourly_people_counts) != 24:
            raise ValueError("시간별 인원 수는 24개 요소를 가진 목록이어야 합니다.")
        
        daily_wind_power = 0
        daily_piezo_power = 0
        hourly_results = []
        
        for hour in range(24):
            wind_speed = hourly_wind_speeds[hour]
            
            people_count = None
            if hourly_people_counts is not None:
                people_count = hourly_people_counts[hour]
            
            # 시간별 발전량 계산
            result = self.calculate_total_power(location, wind_speed, people_count, 1, temp_info)
            hourly_results.append(result)
            
            daily_wind_power += result['wind_power_wh']
            daily_piezo_power += result['piezo_power_wh']
        
        total_power = daily_wind_power + daily_piezo_power
        
        # 가로등 소비 전력 (12시간만 작동)
        streetlight_count = self.streetlight_count.get(location, 0)
        streetlight_consumption = self.led_streetlight_power * streetlight_count * self.led_streetlight_hours
        
        # 발전량과 소비량 차이
        power_balance = total_power - streetlight_consumption
        
        return {
            'location': location,
            'daily_wind_power_wh': round(daily_wind_power, 2),
            'daily_piezo_power_wh': round(daily_piezo_power, 2),
            'daily_total_power_wh': round(total_power, 2),
            'daily_total_power_kwh': round(total_power / 1000, 3),
            'streetlight_consumption_wh': round(streetlight_consumption, 2),
            'streetlight_consumption_kwh': round(streetlight_consumption / 1000, 3),
            'power_balance_wh': round(power_balance, 2),
            'power_balance_kwh': round(power_balance / 1000, 3),
            'is_sufficient': power_balance >= 0,
            'sufficiency_percentage': round((total_power / max(0.1, streetlight_consumption)) * 100, 1) if streetlight_consumption > 0 else float('inf'),
            'hourly_results': hourly_results,
            'temperature_info': temp_info or {}
        }
        
    # 다른 예측 함수들(predict_weekly_power, predict_monthly_power, predict_annual_power)은 
    # 유지하되 temp_info 파라미터 추가 등 필요한 수정만 진행