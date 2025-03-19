"""
ESS(Energy Storage System) 제어 모듈
- 배터리 셀의 충방전 관리
- 전력 생산량에 따른 충방전 속도 자동 조절
- SOC(State of Charge) 모니터링
"""
import time
import numpy as np
from datetime import datetime, timedelta

class ESSController:
    def __init__(self):
        # 기본 설정
        self.cell_capacity = 3000  # mAh (3Ah)
        self.cell_voltage_full = 4.2  # V (완전 충전 전압)
        self.cell_voltage_empty = 3.0  # V (방전 종료 전압)
        self.current_temperature = 298.15  # K (25°C)
        
        # 충방전 상태
        self.current_soc = 0.0  # State of Charge (0.0 ~ 1.0)
        self.current_voltage = 3.0  # V (현재 전압)
        self.charge_current = 0.0  # A (충전 전류)
        self.discharge_current = 0.0  # A (방전 전류)
        
        # 시스템 설정
        self.threshold_power = 25804.8  # Wh (초과 전력 기준)
        self.system_state = "IDLE"  # IDLE, CHARGING, DISCHARGING, REST
        self.rest_start_time = None  # 휴식 시작 시간
        self.rest_duration = 120  # 분 (휴식 시간)
        
        # 배터리 셀 팩 설정
        self.cells_in_series = 7  # 직렬 연결 셀 수
        self.cells_in_parallel = 4  # 병렬 연결 셀 수
        self.total_cells = self.cells_in_series * self.cells_in_parallel
        
        # 방전 설정 (계절별 가로등 작동 시간에 따른 조정)
        self.seasonal_discharge_rates = {
            'winter': 0.0932,  # C-rate (긴 밤)
            'spring': 0.0833,  # C-rate (표준)
            'summer': 0.0734,  # C-rate (짧은 밤)
            'fall': 0.0833    # C-rate (표준)
        }
        self.current_discharge_rate = self.seasonal_discharge_rates['spring']
        
        # 충전 및 방전 내역 기록
        self.charge_history = []
        self.discharge_history = []
        
        # 배터리 전압 변환 계수
        self.voltage_conversion_factor = 2.749  # A

    def update_season(self, month):
        """
        계절에 따른 방전율 업데이트
        
        Args:
            month (int): 월 (1-12)
        """
        if month in [12, 1, 2]:  # 겨울 (12-2월)
            self.current_discharge_rate = self.seasonal_discharge_rates['winter']
        elif month in [3, 4, 5]:  # 봄 (3-5월)
            self.current_discharge_rate = self.seasonal_discharge_rates['spring']
        elif month in [6, 7, 8]:  # 여름 (6-8월)
            self.current_discharge_rate = self.seasonal_discharge_rates['summer']
        else:  # 가을 (9-11월)
            self.current_discharge_rate = self.seasonal_discharge_rates['fall']

    def calculate_ocv(self, soc):
        """
        SOC에 따른 Open Circuit Voltage(OCV) 계산
        
        Args:
            soc (float): 충전 상태 (0.0 ~ 1.0)
            
        Returns:
            float: 전압(V)
        """
        # 간단한 선형 모델 (실제로는 비선형적일 수 있음)
        ocv = self.cell_voltage_empty + soc * (self.cell_voltage_full - self.cell_voltage_empty)
        
        # 실제 배터리는 비선형적이므로 다항식 보정 추가
        # 이 부분은 실제 배터리 데이터에 맞게 조정해야 함
        ocv += 0.1 * np.sin(np.pi * soc)
        
        return round(min(max(ocv, self.cell_voltage_empty), self.cell_voltage_full), 2)
    
    def calculate_soc(self, voltage):
        """
        전압에 따른 SOC 계산 (역계산)
        
        Args:
            voltage (float): 전압(V)
            
        Returns:
            float: SOC (0.0 ~ 1.0)
        """
        # 간단한 선형 모델의 역함수 (근사치)
        soc = (voltage - self.cell_voltage_empty) / (self.cell_voltage_full - self.cell_voltage_empty)
        
        # 비선형 보정의 역함수는 복잡하므로 근사치 사용
        soc = max(0.0, min(1.0, soc))
        
        return round(soc, 2)
    
    def start_cc_charging(self, power_production):
        """
        정전류(CC) 충전 시작
        
        Args:
            power_production (float): 현재 전력 생산량 (Wh)
            
        Returns:
            dict: 충전 상태 정보
        """
        # 변경된 C-rate 계산 (전력 생산량에 따라)
        base_c_rate = 0.1  # 기본 0.1C
        
        # 전력 생산량이 임계값을 초과하는 경우 C-rate 조정
        if power_production > self.threshold_power:
            excess_power = power_production - self.threshold_power
            adjusted_c_rate = base_c_rate * 0.1 / ((6.75e-9 * excess_power) + 0.1)
        else:
            adjusted_c_rate = base_c_rate
            
        # 충전 전류 계산 (C-rate x 용량)
        self.charge_current = adjusted_c_rate * self.cell_capacity / 1000  # A
        
        # 시스템 상태 업데이트
        self.system_state = "CHARGING_CC"
        
        # 충전 로그 기록
        self.charge_history.append({
            'timestamp': datetime.now().isoformat(),
            'mode': 'CC',
            'current': self.charge_current,
            'initial_soc': self.current_soc,
            'initial_voltage': self.current_voltage,
            'c_rate': adjusted_c_rate,
            'power_production': power_production
        })
        
        return {
            'state': self.system_state,
            'charge_current': self.charge_current,
            'c_rate': adjusted_c_rate,
            'soc': self.current_soc,
            'voltage': self.current_voltage,
            'power_production': power_production
        }
    
    def continue_cc_charging(self, duration_seconds):
        """
        정전류(CC) 충전 계속 진행
        
        Args:
            duration_seconds (float): 충전 진행 시간 (초)
            
        Returns:
            dict: 충전 상태 정보
        """
        if self.system_state != "CHARGING_CC":
            return {'error': '정전류 충전 상태가 아닙니다.'}
        
        # 충전량 계산 (A * h)
        charge_amount = self.charge_current * (duration_seconds / 3600)
        
        # SOC 증가량 계산 (충전량 / 용량)
        soc_increase = charge_amount / (self.cell_capacity / 1000)
        
        # SOC 업데이트
        old_soc = self.current_soc
        self.current_soc = min(self.current_soc + soc_increase, 1.0)
        
        # 전압 업데이트
        self.current_voltage = self.calculate_ocv(self.current_soc)
        
        # CC 충전 종료 조건 확인 (전압 >= 4.2V)
        if self.current_voltage >= self.cell_voltage_full:
            self.current_voltage = self.cell_voltage_full
            
            # CV 충전으로 전환
            self.system_state = "CHARGING_CV"
            
            return {
                'state': self.system_state,
                'message': 'CC 충전 완료. CV 충전으로 전환합니다.',
                'old_soc': round(old_soc * 100, 1),
                'new_soc': round(self.current_soc * 100, 1),
                'voltage': self.current_voltage,
                'charge_current': self.charge_current
            }
        
        return {
            'state': self.system_state,
            'old_soc': round(old_soc * 100, 1),
            'new_soc': round(self.current_soc * 100, 1),
            'voltage': self.current_voltage,
            'charge_current': self.charge_current
        }
    
    def continue_cv_charging(self, duration_seconds):
        """
        정전압(CV) 충전 계속 진행
        
        Args:
            duration_seconds (float): 충전 진행 시간 (초)
            
        Returns:
            dict: 충전 상태 정보
        """
        if self.system_state != "CHARGING_CV":
            return {'error': '정전압 충전 상태가 아닙니다.'}
        
        # CV 충전에서는 전류가 지수적으로 감소
        # I(t) = I_initial * exp(-t/tau)
        tau = 3600  # 시간 상수 (초)
        
        # 감소된 전류 계산
        old_current = self.charge_current
        self.charge_current = self.charge_current * np.exp(-duration_seconds / tau)
        
        # SOC 업데이트 (미세한 증가)
        old_soc = self.current_soc
        charge_amount = (old_current + self.charge_current) / 2 * (duration_seconds / 3600)  # 평균 전류 사용
        soc_increase = charge_amount / (self.cell_capacity / 1000)
        self.current_soc = min(self.current_soc + soc_increase, 1.0)
        
        # 전압은 4.2V로 유지
        self.current_voltage = self.cell_voltage_full
        
        # CV 충전 종료 조건 확인 (전류 <= 0.02C mA)
        c_rate_cutoff = 0.02
        current_cutoff = c_rate_cutoff * self.cell_capacity / 1000  # A
        
        if self.charge_current <= current_cutoff:
            # 휴식 모드로 전환
            self.system_state = "REST"
            self.rest_start_time = datetime.now()
            
            # 충전 완료 로그
            self.charge_history[-1]['final_soc'] = self.current_soc
            self.charge_history[-1]['final_voltage'] = self.current_voltage
            self.charge_history[-1]['completed_at'] = datetime.now().isoformat()
            
            return {
                'state': self.system_state,
                'message': 'CV 충전 완료. 휴식 모드로 전환합니다.',
                'soc': round(self.current_soc * 100, 1),
                'voltage': self.current_voltage,
                'charge_current': self.charge_current,
                'rest_duration_minutes': self.rest_duration
            }
        
        return {
            'state': self.system_state,
            'old_soc': round(old_soc * 100, 1),
            'new_soc': round(self.current_soc * 100, 1),
            'voltage': self.current_voltage,
            'old_current': old_current,
            'charge_current': self.charge_current
        }
    
    def check_rest_state(self):
        """
        휴식 상태 확인
        
        Returns:
            dict: 휴식 상태 정보
        """
        if self.system_state != "REST":
            return {'error': '휴식 상태가 아닙니다.'}
        
        current_time = datetime.now()
        elapsed_minutes = (current_time - self.rest_start_time).total_seconds() / 60
        
        if elapsed_minutes >= self.rest_duration:
            # 휴식 완료 후 IDLE 상태로 전환
            old_state = self.system_state
            self.system_state = "IDLE"
            
            return {
                'state': self.system_state,
                'message': f'휴식 완료. {old_state}에서 {self.system_state}로 전환했습니다.',
                'soc': round(self.current_soc * 100, 1),
                'voltage': self.current_voltage,
                'elapsed_minutes': round(elapsed_minutes, 1),
                'rest_duration_minutes': self.rest_duration
            }
        
        return {
            'state': self.system_state,
            'soc': round(self.current_soc * 100, 1),
            'voltage': self.current_voltage,
            'elapsed_minutes': round(elapsed_minutes, 1),
            'rest_duration_minutes': self.rest_duration,
            'remaining_minutes': round(self.rest_duration - elapsed_minutes, 1)
        }
    
    def start_cc_discharging(self, power_production=None):
        """
        정전류(CC) 방전 시작
        
        Args:
            power_production (float, optional): 현재 전력 생산량 (Wh)
            
        Returns:
            dict: 방전 상태 정보
        """
        # 조정된 C-rate 계산 (전력 생산량에 따라)
        base_c_rate = self.current_discharge_rate  # 기본 방전율 (계절에 따라 달라짐)
        
        # 전력 생산량이 임계값을 초과하는 경우 C-rate 조정
        if power_production and power_production > self.threshold_power:
            excess_power = power_production - self.threshold_power
            adjusted_c_rate = base_c_rate * ((6.75e-9 * excess_power) + base_c_rate) / base_c_rate
        else:
            adjusted_c_rate = base_c_rate
            
        # 방전 전류 계산 (C-rate x 용량)
        self.discharge_current = adjusted_c_rate * self.cell_capacity / 1000  # A
        
        # 시스템 상태 업데이트
        self.system_state = "DISCHARGING"
        
        # 방전 로그 기록
        self.discharge_history.append({
            'timestamp': datetime.now().isoformat(),
            'current': self.discharge_current,
            'initial_soc': self.current_soc,
            'initial_voltage': self.current_voltage,
            'c_rate': adjusted_c_rate,
            'power_production': power_production
        })
        
        return {
            'state': self.system_state,
            'discharge_current': self.discharge_current,
            'c_rate': adjusted_c_rate,
            'soc': self.current_soc,
            'voltage': self.current_voltage
        }
    
    def continue_discharging(self, duration_seconds):
        """
        방전 계속 진행
        
        Args:
            duration_seconds (float): 방전 진행 시간 (초)
            
        Returns:
            dict: 방전 상태 정보
        """
        if self.system_state != "DISCHARGING":
            return {'error': '방전 상태가 아닙니다.'}
        
        # 방전량 계산 (A * h)
        discharge_amount = self.discharge_current * (duration_seconds / 3600)
        
        # SOC 감소량 계산 (방전량 / 용량)
        soc_decrease = discharge_amount / (self.cell_capacity / 1000)
        
        # SOC 업데이트
        old_soc = self.current_soc
        self.current_soc = max(self.current_soc - soc_decrease, 0.0)
        
        # 전압 업데이트
        old_voltage = self.current_voltage
        self.current_voltage = self.calculate_ocv(self.current_soc)
        
        # 방전 종료 조건 확인 (SOC <= 0 또는 전압 <= 최소 전압)
        if self.current_soc <= 0 or self.current_voltage <= self.cell_voltage_empty:
            self.current_soc = 0
            self.current_voltage = self.cell_voltage_empty
            
            # 휴식 모드로 전환
            self.system_state = "REST"
            self.rest_start_time = datetime.now()
            
            # 방전 완료 로그
            self.discharge_history[-1]['final_soc'] = self.current_soc
            self.discharge_history[-1]['final_voltage'] = self.current_voltage
            self.discharge_history[-1]['completed_at'] = datetime.now().isoformat()
            
            return {
                'state': self.system_state,
                'message': '방전 완료. 휴식 모드로 전환합니다.',
                'soc': round(self.current_soc * 100, 1),
                'voltage': self.current_voltage,
                'rest_duration_minutes': self.rest_duration
            }
        
        # 출력 전압 변환 (가로등 작동을 위한)
        output_voltage = self.current_voltage * self.cells_in_series  # 직렬 연결된 셀의 전압 합
        output_current = self.discharge_current * self.cells_in_parallel  # 병렬 연결된 셀의 전류 합
        
        # 전압 변환 장치를 통한 최종 출력 (예: DC-DC 컨버터)
        converted_voltage = output_voltage * self.voltage_conversion_factor
        
        return {
            'state': self.system_state,
            'old_soc': round(old_soc * 100, 1),
            'new_soc': round(self.current_soc * 100, 1),
            'old_voltage': old_voltage,
            'cell_voltage': self.current_voltage,
            'battery_pack_voltage': output_voltage,
            'battery_pack_current': output_current,
            'converted_output_voltage': converted_voltage,
            'discharge_current': self.discharge_current
        }
    
    def get_battery_status(self):
        """
        배터리 상태 조회
        
        Returns:
            dict: 배터리 상태 정보
        """
        return {
            'state': self.system_state,
            'soc': round(self.current_soc * 100, 1),
            'voltage': self.current_voltage,
            'charge_current': self.charge_current,
            'discharge_current': self.discharge_current,
            'temperature': self.current_temperature,
            'cell_configuration': f"{self.cells_in_series}S{self.cells_in_parallel}P",
            'total_cells': self.total_cells,
            'capacity': self.cell_capacity * self.cells_in_parallel / 1000,  # Ah
            'pack_voltage': self.current_voltage * self.cells_in_series,  # V
            'rest_info': self._get_rest_info() if self.system_state == "REST" else None
        }
    
    def _get_rest_info(self):
        """
        휴식 상태 정보 조회
        
        Returns:
            dict: 휴식 상태 정보
        """
        if self.system_state != "REST" or not self.rest_start_time:
            return None
            
        current_time = datetime.now()
        elapsed_seconds = (current_time - self.rest_start_time).total_seconds()
        remaining_seconds = max(0, self.rest_duration * 60 - elapsed_seconds)
        
        return {
            'start_time': self.rest_start_time.isoformat(),
            'elapsed_minutes': round(elapsed_seconds / 60, 1),
            'remaining_minutes': round(remaining_seconds / 60, 1),
            'total_duration_minutes': self.rest_duration
        }
    
    def automatic_control(self, power_production, is_nighttime=False):
        """
        자동 제어 - 전력 상황에 따라 충방전 자동 관리
        
        Args:
            power_production (float): 현재 전력 생산량 (Wh)
            is_nighttime (bool): 야간 여부 (가로등 작동 필요 시간)
            
        Returns:
            dict: 제어 결과
        """
        # 현재 상태에 따른 처리
        if self.system_state == "REST":
            # 휴식 상태 점검
            rest_status = self.check_rest_state()
            if rest_status.get('state') == "IDLE":
                # 휴식 종료, 다음 단계 진행
                pass
            else:
                # 아직 휴식 중
                return rest_status
        
        # 야간이면 방전 (가로등 작동)
        if is_nighttime:
            if self.system_state != "DISCHARGING" and self.current_soc > 0:
                # 방전 시작
                return self.start_cc_discharging(power_production)
            elif self.system_state == "DISCHARGING":
                # 방전 계속
                return self.continue_discharging(60)  # 60초 동안 방전
            else:
                return {
                    'state': self.system_state,
                    'message': '방전할 수 없습니다. 배터리가 비어 있거나 다른 상태입니다.',
                    'soc': round(self.current_soc * 100, 1)
                }
        
        # 주간 (충전 시간)
        else:
            # 생산량이 임계값보다 크면 C-rate 조정
            if power_production > self.threshold_power:
                # SOC가 이미 100%면 충전 불필요
                if self.current_soc >= 1.0:
                    return {
                        'state': self.system_state,
                        'message': '배터리가 이미 완전히 충전되었습니다.',
                        'soc': 100.0,
                        'power_production': power_production
                    }
                
                # 충전 상태에 따른 처리
                if self.system_state == "IDLE":
                    # CC 충전 시작
                    return self.start_cc_charging(power_production)
                elif self.system_state == "CHARGING_CC":
                    # CC 충전 계속
                    return self.continue_cc_charging(60)  # 60초 동안 충전
                elif self.system_state == "CHARGING_CV":
                    # CV 충전 계속
                    return self.continue_cv_charging(60)  # 60초 동안 충전
            
            # 생산량이 임계값보다 작으면 기본 충전
            else:
                # SOC < 100%일 때만 충전
                if self.current_soc < 1.0 and self.system_state == "IDLE":
                    # 기본 CC 충전 시작
                    return self.start_cc_charging(power_production)
                elif self.system_state == "CHARGING_CC":
                    # CC 충전 계속
                    return self.continue_cc_charging(60)
                elif self.system_state == "CHARGING_CV":
                    # CV 충전 계속
                    return self.continue_cv_charging(60)
            
            # 그 외 상태는 유지
            return {
                'state': self.system_state,
                'message': '현재 상태를 유지합니다.',
                'soc': round(self.current_soc * 100, 1),
                'voltage': self.current_voltage,
                'power_production': power_production
            }

    def simulate_day_cycle(self, daily_power_data, start_hour=6, end_hour=18):
        """
        하루 충방전 사이클 시뮬레이션
        
        Args:
            daily_power_data (list): 시간별 발전량 데이터 (24개 요소)
            start_hour (int): 주간 시작 시간
            end_hour (int): 주간 종료 시간
            
        Returns:
            dict: 시뮬레이션 결과
        """
        if len(daily_power_data) != 24:
            return {'error': '시간별 발전량 데이터는 24개 요소를 가진 목록이어야 합니다.'}
        
        simulation_results = []
        
        # 24시간 시뮬레이션
        for hour in range(24):
            is_nighttime = hour < start_hour or hour >= end_hour
            power_production = daily_power_data[hour]
            
            # 10분 단위로 제어 (6회/시간)
            for minute in range(0, 60, 10):
                result = self.automatic_control(power_production / 6, is_nighttime)
                
                # 결과 기록
                simulation_results.append({
                    'hour': hour,
                    'minute': minute,
                    'is_nighttime': is_nighttime,
                    'power_production': power_production / 6,  # 10분 동안의 생산량
                    'state': result.get('state'),
                    'soc': result.get('soc', round(self.current_soc * 100, 1)),
                    'voltage': result.get('voltage', self.current_voltage)
                })
        
        # 종합 결과
        summary = {
            'initial_soc': simulation_results[0]['soc'],
            'final_soc': simulation_results[-1]['soc'],
            'total_charge_cycles': len(self.charge_history),
            'total_discharge_cycles': len(self.discharge_history),
            'hourly_results': []
        }
        
        # 시간별 요약
        for hour in range(24):
            hour_results = [r for r in simulation_results if r['hour'] == hour]
            summary['hourly_results'].append({
                'hour': hour,
                'is_nighttime': hour_results[0]['is_nighttime'],
                'power_production': sum(r['power_production'] for r in hour_results),
                'start_soc': hour_results[0]['soc'],
                'end_soc': hour_results[-1]['soc'],
                'soc_change': hour_results[-1]['soc'] - hour_results[0]['soc']
            })
        
        return {
            'summary': summary,
            'detailed_results': simulation_results
        }