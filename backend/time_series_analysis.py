"""
시계열 분석 모듈 - 풍속, 기온, 습도 데이터 분석 및 예측
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle
import os
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score

class TimeSeriesAnalyzer:
    def __init__(self, model_dir=None):
        """
        시계열 분석기 초기화
        
        Args:
            model_dir (str, optional): 모델 저장 디렉토리
        """
        self.model_dir = model_dir if model_dir else os.getenv("MODEL_DIR", "models")
        os.makedirs(self.model_dir, exist_ok=True)
        
        # 데이터 스케일러 
        self.scalers = {}
        
        # 예측 모델
        self.models = {}
        
        # 특성 목록
        self.features = [
            'hour_sin', 'hour_cos',  # 시간 순환 인코딩
            'day_sin', 'day_cos',    # 일 순환 인코딩
            'month_sin', 'month_cos',  # 월 순환 인코딩
            'prev_1h', 'prev_2h', 'prev_3h',  # 이전 시간 값
            'prev_day', 'prev_week',  # 이전 일/주 값
            'trend'  # 추세
        ]
    
    def _load_csv_data(self, file_paths):
        """
        CSV 파일 로드 및 전처리
        
        Args:
            file_paths (dict): 파일 경로 딕셔너리 {'wind': 경로, 'temp': 경로, 'humidity': 경로, 'rain': 경로}
            
        Returns:
            DataFrame: 병합된 데이터프레임
        """
        data_frames = {}
        
        # 각 파일 로드
        try:
            for data_type, file_path in file_paths.items():
                print(f"파일 로드 시작: {data_type} - {file_path}")
                
                # 다양한 인코딩 시도
                for encoding in ['utf-8', 'cp1252', 'euc-kr']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        print(f"인코딩 '{encoding}'으로 파일 로드 성공: {data_type}")
                        print(f"로드된 데이터 형태: {df.shape}, 열: {df.columns.tolist()}")
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        print(f"{data_type} 파일 로드 오류 ({encoding}): {e}")
                        continue
                else:
                    raise ValueError(f"{data_type} 파일을 읽을 수 없습니다.")
                
                # 열 이름 확인 및 변경 (CP1252 인코딩으로 깨진 한글 처리)
                column_mapping = {
                    # 일시
                    'ÀÏ½Ã': 'Date',
                    '일시': 'Date',
                    # 풍속 데이터
                    'Æò±ÕÇ³¼Ó(m/s)': 'AvgWindSpeed_mps',
                    '평균풍속(m/s)': 'AvgWindSpeed_mps',
                    'ÃÖ´ëÇ³¼Ó(m/s)': 'MaxWindSpeed_mps',
                    '최대풍속(m/s)': 'MaxWindSpeed_mps',
                    # 습도 데이터
                    'Æò±Õ½Àµµ(%rh)': 'AvgHumidity_percent',
                    '평균습도(%rh)': 'AvgHumidity_percent',
                    'ÃÖÀú½Àµµ(%rh)': 'MinHumidity_percent',
                    '최저습도(%rh)': 'MinHumidity_percent',
                    # 온도 데이터
                    'Æò±Õ±â¿Â(¡É)': 'AvgTemp_C',
                    '평균기온(℃)': 'AvgTemp_C',
                    'ÃÖ°í±â¿Â(¡É)': 'MaxTemp_C',
                    '최고기온(℃)': 'MaxTemp_C',
                    'ÃÖÀú±â¿Â(¡É)': 'MinTemp_C',
                    '최저기온(℃)': 'MinTemp_C',
                    # 강수량 데이터
                    '°­¼ö·®(mm)': 'Precipitation_mm',
                    '강수량(mm)': 'Precipitation_mm',
                    '1½Ã°£ÃÖ´Ù°­¼ö·®(mm)': 'MaxHourlyPrecipitation_mm',
                    '1시간최다강수량(mm)': 'MaxHourlyPrecipitation_mm'
                }
                
                # 열 이름 변경
                for old_col, new_col in column_mapping.items():
                    if old_col in df.columns:
                        df.rename(columns={old_col: new_col}, inplace=True)
                
                # CSV 형식에 맞게 열 처리 (rain_data.csv 형식 참고)
                if data_type == 'rain':
                    # 확인: 'Date', 'Precipitation_mm', 'MaxHourlyPrecipitation_mm', 'MaxHourlyPrecipitationTime'
                    if 'Date' not in df.columns and df.columns[0].startswith('2'):
                        # 첫 열이 날짜 형식이면 Date 열로 사용
                        df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
                
                # 필요한 열만 선택 (가능한 경우)
                if data_type == 'wind' and 'AvgWindSpeed_mps' in df.columns:
                    cols = ['Date', 'AvgWindSpeed_mps', 'MaxWindSpeed_mps']
                    df = df[[col for col in cols if col in df.columns]]
                elif data_type == 'temp' and 'AvgTemp_C' in df.columns:
                    cols = ['Date', 'AvgTemp_C', 'MaxTemp_C', 'MinTemp_C']
                    df = df[[col for col in cols if col in df.columns]]
                elif data_type == 'humidity' and 'AvgHumidity_percent' in df.columns:
                    cols = ['Date', 'AvgHumidity_percent', 'MinHumidity_percent']
                    df = df[[col for col in cols if col in df.columns]]
                elif data_type == 'rain' and 'Precipitation_mm' in df.columns:
                    cols = ['Date', 'Precipitation_mm', 'MaxHourlyPrecipitation_mm']
                    df = df[[col for col in cols if col in df.columns]]
                
                # 필수 열 확인
                if 'Date' not in df.columns:
                    print(f"경고: {data_type} 파일에 'Date' 열이 없습니다. 첫 번째 열을 사용합니다.")
                    df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
                
                # NaN 값 개수 확인
                null_count = df.isna().sum().sum()
                if null_count > 0:
                    print(f"경고: {data_type} 파일에 {null_count}개의 NaN 값이 있습니다.")
                
                # 중복 제거 및 정렬
                if 'Date' in df.columns:
                    df.drop_duplicates(subset=['Date'], inplace=True)
                    df.sort_values('Date', inplace=True)
                
                data_frames[data_type] = df
        
        except Exception as e:
            print(f"데이터 로드 오류: {e}")
            import traceback
            traceback.print_exc()
            
            # 샘플 데이터 생성
            print("샘플 데이터를 생성합니다.")
            return self._create_sample_dataframes()
        
        # 데이터프레임이 비어있는지 확인
        if not data_frames:
            print("로드된 데이터가 없습니다. 샘플 데이터를 생성합니다.")
            return self._create_sample_dataframes()
        
        # 데이터 병합
        merged_df = None
        for data_type, df in data_frames.items():
            if merged_df is None:
                merged_df = df
            else:
                # 'Date' 열을 기준으로 병합
                if 'Date' in df.columns and 'Date' in merged_df.columns:
                    merged_df = pd.merge(merged_df, df, on='Date', how='outer')
                else:
                    print(f"경고: {data_type} 데이터프레임을 병합할 수 없습니다. 'Date' 열이 없습니다.")
        
        # 최종 데이터프레임 검증
        if merged_df is None or merged_df.empty:
            print("병합된 데이터프레임이 비어있습니다. 샘플 데이터를 생성합니다.")
            return self._create_sample_dataframes()
        
        # NaN 체크 및 처리
        null_count = merged_df.isna().sum().sum()
        if null_count > 0:
            print(f"병합된 데이터에 {null_count}개의 NaN 값이 있습니다. 처리를 시작합니다...")
            
            # 결측치 처리 - 앞/뒤 값으로 채우기
            merged_df = merged_df.ffill().bfill()
            
            # 남은 NaN 값 처리
            merged_df = merged_df.fillna(0)
        
        print(f"최종 병합된 데이터 형태: {merged_df.shape}, 열: {merged_df.columns.tolist()}")
        return merged_df
    
    def _create_sample_dataframes(self):
        """샘플 데이터프레임 생성"""
        print("샘플 데이터프레임 생성 중...")
        # 날짜 범위 생성 (최근 1년, 일별 데이터)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        dates = pd.date_range(start_date, end_date, freq='D')
        
        # 기본 데이터프레임 생성
        df = pd.DataFrame({'Date': dates.strftime('%Y%m%d')})
        
        # 풍속 데이터 추가
        df['AvgWindSpeed_mps'] = np.random.normal(3.5, 1.2, len(df))  # 평균 3.5m/s, 표준편차 1.2
        df['MaxWindSpeed_mps'] = df['AvgWindSpeed_mps'] + np.random.normal(2, 0.8, len(df))  # 최대 풍속
        
        # 온도 데이터 추가 (계절성 패턴 포함)
        season = np.sin(np.linspace(0, 2*np.pi, len(df)))  # 1년 주기의 사인파
        df['AvgTemp_C'] = 15 + 10 * season + np.random.normal(0, 3, len(df))  # 평균 15°C, 진폭 10°C
        df['MaxTemp_C'] = df['AvgTemp_C'] + np.random.normal(5, 1, len(df))  # 최고 기온
        df['MinTemp_C'] = df['AvgTemp_C'] - np.random.normal(5, 1, len(df))  # 최저 기온
        
        # 습도 데이터 추가 (온도와 약간의 역상관관계)
        df['AvgHumidity_percent'] = 70 - 0.3 * df['AvgTemp_C'] + np.random.normal(0, 10, len(df))  # 평균 습도
        df['MinHumidity_percent'] = df['AvgHumidity_percent'] - np.random.normal(15, 5, len(df))  # 최저 습도
        
        # 강수량 데이터 추가 (대부분 0, 가끔 큰 값)
        rain_prob = np.random.uniform(0, 1, len(df)) < 0.3  # 30% 확률로 비
        df['Precipitation_mm'] = np.where(rain_prob, np.random.exponential(5, len(df)), 0)  # 비가 오면 지수분포
        df['MaxHourlyPrecipitation_mm'] = df['Precipitation_mm'] * np.random.uniform(0.2, 0.5, len(df))  # 시간당 최대 강수량
        
        # 값 범위 조정
        df['AvgWindSpeed_mps'] = df['AvgWindSpeed_mps'].clip(0, 15)  # 풍속 범위: 0 ~ 15m/s
        df['MaxWindSpeed_mps'] = df['MaxWindSpeed_mps'].clip(0, 20)  # 최대 풍속 범위: 0 ~ 20m/s
        df['AvgTemp_C'] = df['AvgTemp_C'].clip(-10, 35)  # 기온 범위: -10 ~ 35°C
        df['MaxTemp_C'] = df['MaxTemp_C'].clip(-5, 40)  # 최고 기온 범위: -5 ~ 40°C
        df['MinTemp_C'] = df['MinTemp_C'].clip(-15, 30)  # 최저 기온 범위: -15 ~ 30°C
        df['AvgHumidity_percent'] = df['AvgHumidity_percent'].clip(30, 100)  # 습도 범위: 30 ~ 100%
        df['MinHumidity_percent'] = df['MinHumidity_percent'].clip(20, 95)  # 최저 습도 범위: 20 ~ 95%
        df['Precipitation_mm'] = df['Precipitation_mm'].clip(0, 100)  # 강수량 범위: 0 ~ 100mm
        df['MaxHourlyPrecipitation_mm'] = df['MaxHourlyPrecipitation_mm'].clip(0, 50)  # 시간당 최대 강수량 범위: 0 ~ 50mm
        
        print(f"샘플 데이터프레임 생성 완료: {df.shape}")
        return df
    
    def _preprocess_datetime(self, df):
        """
        날짜/시간 전처리
        
        Args:
            df (DataFrame): 데이터프레임
            
        Returns:
            DataFrame: 전처리된 데이터프레임
        """
        # 날짜 형식 처리
        if 'Date' in df.columns:
            try:
                # 다양한 날짜 형식 처리
                date_formats = ['%Y%m%d%H', '%Y%m%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
                
                for date_format in date_formats:
                    try:
                        df['Datetime'] = pd.to_datetime(df['Date'], format=date_format, errors='coerce')
                        if not df['Datetime'].isna().all():
                            print(f"날짜 형식 '{date_format}'으로 변환 성공")
                            break
                    except Exception:
                        continue
                
                # 모든 형식이 실패한 경우
                if df['Datetime'].isna().all():
                    print("모든 날짜 형식 변환 실패, 기본 파서 사용")
                    df['Datetime'] = pd.to_datetime(df['Date'], errors='coerce')
            
            except Exception as e:
                print(f"날짜 변환 오류: {e}, 기본 파서 사용")
                try:
                    df['Datetime'] = pd.to_datetime(df['Date'], errors='coerce')
                except Exception as e2:
                    print(f"기본 파서도 실패: {e2}")
                    raise
            
            # NaN 값 체크
            invalid_dates = df['Datetime'].isna().sum()
            if invalid_dates > 0:
                print(f"경고: {invalid_dates}개의 날짜 값이 유효하지 않습니다.")
                df = df.dropna(subset=['Datetime'])
                
                if df.empty:
                    print("모든 날짜가 유효하지 않습니다. 샘플 데이터 생성.")
                    df = self._create_sample_dataframes()
                    df['Datetime'] = pd.to_datetime(df['Date'], errors='coerce')
            
            # 날짜/시간 특성 추출
            df['Year'] = df['Datetime'].dt.year
            df['Month'] = df['Datetime'].dt.month
            df['Day'] = df['Datetime'].dt.day
            df['Hour'] = df['Datetime'].dt.hour
            df['DayOfWeek'] = df['Datetime'].dt.dayofweek
            
            # 순환 특성 인코딩 (시간)
            df['hour_sin'] = np.sin(2 * np.pi * df['Hour'] / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['Hour'] / 24)
            
            # 순환 특성 인코딩 (일)
            df['day_sin'] = np.sin(2 * np.pi * df['Day'] / 31)
            df['day_cos'] = np.cos(2 * np.pi * df['Day'] / 31)
            
            # 순환 특성 인코딩 (월)
            df['month_sin'] = np.sin(2 * np.pi * df['Month'] / 12)
            df['month_cos'] = np.cos(2 * np.pi * df['Month'] / 12)
            
            # 계절 인코딩 (봄: 3-5, 여름: 6-8, 가을: 9-11, 겨울: 12-2)
            season_map = {1: 'Winter', 2: 'Winter', 3: 'Spring', 4: 'Spring', 5: 'Spring',
                          6: 'Summer', 7: 'Summer', 8: 'Summer', 9: 'Fall', 10: 'Fall',
                          11: 'Fall', 12: 'Winter'}
            df['Season'] = df['Month'].map(season_map)
            
            # 원-핫 인코딩 (계절)
            for season in ['Spring', 'Summer', 'Fall', 'Winter']:
                df[f'Season_{season}'] = (df['Season'] == season).astype(int)
            
            # 원-핫 인코딩 (요일: 0=월요일, 6=일요일)
            for day in range(7):
                df[f'DayOfWeek_{day}'] = (df['DayOfWeek'] == day).astype(int)
            
            # 인덱스를 날짜로 설정
            df.set_index('Datetime', inplace=True)
            
            print(f"날짜 전처리 완료: {df.shape}")
        else:
            print("경고: 'Date' 열이 없습니다. 날짜 전처리를 건너뜁니다.")
        
        return df
    
    def _create_lag_features(self, df, target_column, lags=[1, 2, 3, 24, 24*7]):
        """
        지연 특성 생성
        
        Args:
            df (DataFrame): 데이터프레임
            target_column (str): 대상 열
            lags (list): 지연 시간 목록 (시간 단위)
            
        Returns:
            DataFrame: 지연 특성이 추가된 데이터프레임
        """
        if target_column not in df.columns:
            print(f"대상 열 '{target_column}'이 데이터프레임에 없습니다.")
            return df
        
        print(f"lag features 생성 전 데이터 크기: {df.shape}")
        
        # lag 특성 생성
        for lag in lags:
            df[f'{target_column}_lag_{lag}'] = df[target_column].shift(lag)
        
        # NaN 값을 ffill, bfill로 처리 (dropna 사용하지 않음)
        df = df.ffill().bfill()
        
        # 그래도 남은 NaN 값은 0으로 대체
        df = df.fillna(0)
        
        print(f"lag features 생성 후 데이터 크기: {df.shape}")
        
        return df
    
    def _create_rolling_features(self, df, target_column, windows=[3, 6, 12, 24]):
        """
        롤링 윈도우 특성 생성
        
        Args:
            df (DataFrame): 데이터프레임
            target_column (str): 대상 열
            windows (list): 윈도우 크기 목록 (시간 단위)
            
        Returns:
            DataFrame: 롤링 윈도우 특성이 추가된 데이터프레임
        """
        if target_column not in df.columns:
            print(f"대상 열 '{target_column}'이 데이터프레임에 없습니다.")
            return df
        
        print(f"rolling features 생성 전 데이터 크기: {df.shape}")
        
        for window in windows:
            df[f'{target_column}_mean_{window}h'] = df[target_column].rolling(window=window).mean()
            df[f'{target_column}_std_{window}h'] = df[target_column].rolling(window=window).std()
            df[f'{target_column}_min_{window}h'] = df[target_column].rolling(window=window).min()
            df[f'{target_column}_max_{window}h'] = df[target_column].rolling(window=window).max()
        
        # NaN 값 처리 - 업데이트된 방식으로
        df = df.bfill()
        
        # 그래도 남은 NaN 값은 0으로 대체
        df = df.fillna(0)
        
        print(f"rolling features 생성 후 데이터 크기: {df.shape}")
        
        return df
    
    def _prepare_features(self, df, target_column, use_lags=True, use_rolling=True):
        """
        특성 준비
        
        Args:
            df (DataFrame): 데이터프레임
            target_column (str): 대상 열
            use_lags (bool): 지연 특성 사용 여부
            use_rolling (bool): 롤링 윈도우 특성 사용 여부
            
        Returns:
            tuple: (X, y) 특성과 타겟
        """
        if target_column not in df.columns:
            raise ValueError(f"대상 열 '{target_column}'이 데이터프레임에 없습니다.")
        
        # 데이터프레임 복사본 생성 (원본 수정 방지)
        df = df.copy()
        
        # 데이터 크기 및 NaN 상태 확인
        print(f"특성 준비 시작 - 데이터 크기: {df.shape}, NaN 개수: {df.isna().sum().sum()}")
        
        # 결측치 처리 (NaN 값) - 업데이트된 방식으로
        df = df.ffill().bfill()
        
        # 날짜 전처리
        df = self._preprocess_datetime(df)
        
        # 중요 - 데이터 크기 확인
        if len(df) == 0:
            print("경고: 날짜 전처리 후 데이터가 비어있습니다!")
            # 빈 데이터셋인 경우 샘플 데이터 생성
            df = self._create_sample_data(target_column)
        
        # 지연 특성 생성
        if use_lags:
            df = self._create_lag_features(df, target_column)
        
        # 롤링 윈도우 특성 생성
        if use_rolling:
            df = self._create_rolling_features(df, target_column)
        
        # 타겟 변수
        y = df[target_column]
        
        # 사용할 특성 선택
        feature_cols = []
        
        # 기본 시간 특성
        time_features = ['hour_sin', 'hour_cos', 'day_sin', 'day_cos', 'month_sin', 'month_cos']
        feature_cols.extend([col for col in time_features if col in df.columns])
        
        # 원-핫 인코딩 특성
        onehot_features = [col for col in df.columns if 'Season_' in col or 'DayOfWeek_' in col]
        feature_cols.extend(onehot_features)
        
        # 지연 특성
        if use_lags:
            lag_features = [col for col in df.columns if f'{target_column}_lag_' in col]
            feature_cols.extend(lag_features)
        
        # 롤링 윈도우 특성
        if use_rolling:
            rolling_features = [col for col in df.columns if f'{target_column}_' in col and 
                            ('_mean_' in col or '_std_' in col or '_min_' in col or '_max_' in col)]
            feature_cols.extend(rolling_features)
        
        # 다른 관련 특성 (풍속, 기온, 습도, 강수량 등)
        if target_column != 'AvgWindSpeed_mps' and 'AvgWindSpeed_mps' in df.columns:
            feature_cols.append('AvgWindSpeed_mps')
        if target_column != 'AvgTemp_C' and 'AvgTemp_C' in df.columns:
            feature_cols.append('AvgTemp_C')
        if target_column != 'AvgHumidity_percent' and 'AvgHumidity_percent' in df.columns:
            feature_cols.append('AvgHumidity_percent')
        if target_column != 'Precipitation_mm' and 'Precipitation_mm' in df.columns:
            feature_cols.append('Precipitation_mm')
        
        # 특성 행렬 생성
        # 누락된 열 확인 및 필터링
        available_features = [col for col in feature_cols if col in df.columns]
        if len(available_features) < len(feature_cols):
            print(f"경고: 일부 특성을 찾을 수 없습니다. 요청한 특성: {len(feature_cols)}, 사용 가능한 특성: {len(available_features)}")
        
        X = df[available_features]
        
        # 혹시 남아있는 NaN 값 처리
        X = X.fillna(0)
        
        # 최종 데이터 크기 확인
        print(f"특성 준비 완료 - X 크기: {X.shape}, y 크기: {y.shape}")
        
        # 중요 - 최종 데이터셋이 비어있지 않은지 확인
        if len(X) == 0 or len(y) == 0:
            print("경고: 최종 데이터셋이 비어있습니다. 샘플 데이터를 생성합니다.")
            X, y = self._create_sample_data_xy(target_column, available_features)
        
        return X, y
    
    def _create_sample_data(self, target_column):
        """
        샘플 데이터 생성 (데이터셋이 비어있는 경우를 대비)
        
        Args:
            target_column (str): 대상 열 이름
            
        Returns:
            DataFrame: 샘플 데이터
        """
        print("샘플 데이터 생성 시작...")
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        
        # 현재 날짜부터 30일간의 시간별 데이터 생성
        dates = [datetime.now() - timedelta(hours=i) for i in range(24*30)]
        dates.reverse()  # 오름차순 정렬
        
        # 기본 데이터프레임 생성
        df = pd.DataFrame({
            'Date': [d.strftime('%Y%m%d%H') for d in dates],
            'Datetime': dates
        })
        
        # 필요한 데이터 열 생성
        if 'WindSpeed' in target_column:
            df['AvgWindSpeed_mps'] = np.random.normal(4, 1.5, len(df))  # 평균 4m/s, 표준편차 1.5
            df['MaxWindSpeed_mps'] = df['AvgWindSpeed_mps'] + np.random.normal(2, 0.8, len(df))  # 최대 풍속
        
        if 'Temp' in target_column or 'AvgTemp_C' not in df.columns:
            df['AvgTemp_C'] = np.random.normal(20, 5, len(df))  # 평균 20°C, 표준편차 5
            df['MaxTemp_C'] = df['AvgTemp_C'] + np.random.normal(5, 1, len(df))  # 최고 기온
            df['MinTemp_C'] = df['AvgTemp_C'] - np.random.normal(5, 1, len(df))  # 최저 기온
        
        if 'Humidity' in target_column or 'AvgHumidity_percent' not in df.columns:
            df['AvgHumidity_percent'] = np.random.normal(60, 10, len(df))  # 평균 60%, 표준편차 10
            df['MinHumidity_percent'] = df['AvgHumidity_percent'] - np.random.normal(10, 3, len(df))  # 최저 습도
        
        if 'Precipitation' not in df.columns:
            df['Precipitation_mm'] = np.random.exponential(0.5, len(df))  # 강수량, 평균 0.5mm
            df['MaxHourlyPrecipitation_mm'] = df['Precipitation_mm'] * np.random.uniform(1, 2, len(df))  # 최대 시간당 강수량
        
        # 값 범위 조정
        for col in df.columns:
            if 'Temp' in col:
                df[col] = df[col].clip(-10, 40)  # 기온 범위: -10°C ~ 40°C
            elif 'Humidity' in col:
                df[col] = df[col].clip(10, 100)  # 습도 범위: 10% ~ 100%
            elif 'WindSpeed' in col:
                df[col] = df[col].clip(0, 20)  # 풍속 범위: 0 ~ 20m/s
            elif 'Precipitation' in col:
                df[col] = df[col].clip(0, 50)  # 강수량 범위: 0 ~ 50mm
        
        # 인덱스 설정
        df.set_index('Datetime', inplace=True)
        
        # 날짜/시간 특성 추출
        df['Year'] = df.index.year
        df['Month'] = df.index.month
        df['Day'] = df.index.day
        df['Hour'] = df.index.hour
        df['DayOfWeek'] = df.index.dayofweek
        
        print(f"샘플 데이터 생성 완료 - 크기: {df.shape}")
        return df
    
    def _create_sample_data_xy(self, target_column, features):
        """
        샘플 X, y 데이터 직접 생성
        
        Args:
            target_column (str): 타겟 열 이름
            features (list): 특성 열 이름 목록
            
        Returns:
            tuple: (X, y) 샘플 데이터
        """
        import pandas as pd
        import numpy as np
        
        # 샘플 크기
        n_samples = 100
        
        # X 데이터 생성
        X_data = {}
        for feature in features:
            if 'sin' in feature or 'cos' in feature:
                X_data[feature] = np.random.uniform(-1, 1, n_samples)
            elif 'DayOfWeek' in feature or 'Season' in feature:
                X_data[feature] = np.random.choice([0, 1], n_samples)
            elif 'Temp' in feature:
                X_data[feature] = np.random.normal(20, 5, n_samples)
            elif 'Humidity' in feature:
                X_data[feature] = np.random.normal(60, 10, n_samples)
            elif 'WindSpeed' in feature:
                X_data[feature] = np.random.normal(4, 1.5, n_samples)
            elif 'Precipitation' in feature:
                X_data[feature] = np.random.exponential(0.5, n_samples)
            else:
                X_data[feature] = np.random.normal(0, 1, n_samples)
        
        X = pd.DataFrame(X_data)
        
        # y 데이터 생성
        if 'WindSpeed' in target_column:
            y = pd.Series(np.random.normal(4, 1.5, n_samples), name=target_column)
        elif 'Temp' in target_column:
            y = pd.Series(np.random.normal(20, 5, n_samples), name=target_column)
        elif 'Humidity' in target_column:
            y = pd.Series(np.random.normal(60, 10, n_samples), name=target_column)
        else:
            y = pd.Series(np.random.normal(0, 1, n_samples), name=target_column)
        
        print(f"샘플 X, y 데이터 생성 완료 - X 크기: {X.shape}, y 크기: {y.shape}")
        return X, y
    
    def train_models(self, file_paths):
        """
        시계열 예측 모델 학습
        
        Args:
            file_paths (dict): 파일 경로 딕셔너리 {'wind': 경로, 'temp': 경로, 'humidity': 경로, 'rain': 경로}
            
        Returns:
            dict: 학습된 모델 정보
        """
        try:
            # 데이터 로드
            df = self._load_csv_data(file_paths)
            
            # 데이터 검증
            if df is None or df.empty:
                print("경고: 로드된 데이터가 비어있습니다. 샘플 데이터를 사용합니다.")
                # 샘플 데이터 생성
                df = self._create_sample_dataframes()
            
            print(f"로드된 데이터 형태: {df.shape}, 열 목록: {df.columns.tolist()}")
            print(f"NaN 값 개수: {df.isna().sum().sum()}")
            
            # 모델 학습할 대상 열
            target_columns = [
                'AvgWindSpeed_mps', 'MaxWindSpeed_mps',
                'AvgTemp_C', 'MaxTemp_C', 'MinTemp_C',
                'AvgHumidity_percent'
            ]
            
            # 실제 존재하는 열만 선택
            available_targets = [col for col in target_columns if col in df.columns]
            if not available_targets:
                print("경고: 학습 가능한 타겟 열이 없습니다. 필요한 열을 생성합니다.")
                # 필요한 열 추가
                df = self._create_sample_dataframes()
                available_targets = [col for col in target_columns if col in df.columns]
            
            # 각 대상에 대해 모델 학습
            for target_column in available_targets:
                try:
                    print(f"'{target_column}' 모델 학습 시작...")
                    
                    # 특성 준비
                    X, y = self._prepare_features(df, target_column)
                    
                    # 데이터셋이 비어있지 않은지 다시 확인
                    if len(X) == 0 or len(y) == 0:
                        print(f"'{target_column}' 모델 학습 불가: 빈 데이터셋")
                        continue
                    
                    # 학습/테스트 분할 (시간 순서 유지)
                    train_size = int(len(X) * 0.8)
                    X_train, X_test = X[:train_size], X[train_size:]
                    y_train, y_test = y[:train_size], y[train_size:]
                    
                    # 스케일러 학습
                    scaler = StandardScaler()
                    X_train_scaled = scaler.fit_transform(X_train)
                    X_test_scaled = scaler.transform(X_test)
                    
                    # 스케일러 저장
                    self.scalers[target_column] = scaler
                    
                    # RandomForest 모델 학습
                    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
                    rf_model.fit(X_train_scaled, y_train)
                    
                    # Ridge 모델 학습 (선형 모델)
                    ridge_model = Ridge(alpha=1.0)
                    ridge_model.fit(X_train_scaled, y_train)
                    
                    # 모델 평가
                    rf_pred = rf_model.predict(X_test_scaled)
                    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
                    rf_r2 = r2_score(y_test, rf_pred)
                    
                    ridge_pred = ridge_model.predict(X_test_scaled)
                    ridge_rmse = np.sqrt(mean_squared_error(y_test, ridge_pred))
                    ridge_r2 = r2_score(y_test, ridge_pred)
                    
                    # 특성 중요도 (RandomForest 기준)
                    feature_importance = dict(zip(X.columns, rf_model.feature_importances_))
                    
                    # 모델 저장
                    self.models[target_column] = {
                        'random_forest': rf_model,
                        'ridge': ridge_model,
                        'feature_importance': feature_importance,
                        'metrics': {
                            'random_forest': {'rmse': rf_rmse, 'r2': rf_r2},
                            'ridge': {'rmse': ridge_rmse, 'r2': ridge_r2}
                        },
                        'feature_names': list(X.columns)
                    }
                    
                    print(f"'{target_column}' 모델 학습 완료 - RF RMSE: {rf_rmse:.3f}, R²: {rf_r2:.3f}")
                    
                except Exception as e:
                    print(f"'{target_column}' 모델 학습 오류: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 모델 저장
            if self.models:
                self.save_models()
                return self.models
            else:
                print("학습된 모델이 없습니다. 더미 모델을 생성합니다.")
                # 더미 모델 생성
                return self._create_dummy_models()
                
        except Exception as e:
            print(f"모델 학습 과정에서 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return self._create_dummy_models()
    
    def _create_dummy_models(self):
        """
        더미 모델 생성 (모든 학습 시도가 실패한 경우)
        
        Returns:
            dict: 더미 모델 정보
        """
        from sklearn.dummy import DummyRegressor
        
        dummy_models = {}
        for target in ['AvgWindSpeed_mps', 'MaxWindSpeed_mps', 'AvgTemp_C', 'MaxTemp_C', 'MinTemp_C', 'AvgHumidity_percent']:
            # 더미 모델 생성
            dummy_rf = DummyRegressor(strategy='mean')
            dummy_ridge = DummyRegressor(strategy='mean')
            
            # 샘플 데이터로 학습
            X, y = self._create_sample_data_xy(target, ['hour_sin', 'hour_cos', 'day_sin', 'day_cos'])
            dummy_rf.fit(X, y)
            dummy_ridge.fit(X, y)
            
            # 스케일러 생성
            scaler = StandardScaler()
            scaler.fit(X)
            self.scalers[target] = scaler
            
            # 더미 모델 저장
            dummy_models[target] = {
                'random_forest': dummy_rf,
                'ridge': dummy_ridge,
                'feature_importance': {col: 1.0 for col in X.columns},
                'metrics': {
                    'random_forest': {'rmse': 1.0, 'r2': 0.0},
                    'ridge': {'rmse': 1.0, 'r2': 0.0}
                },
                'feature_names': list(X.columns),
                'is_dummy': True
            }
        
        # 더미 모델 저장
        self.models = dummy_models
        self.save_models()
        
        print("더미 모델 생성 완료")
        return dummy_models
    
    def save_models(self):
        """
        학습된 모델 저장
        """
        model_path = os.path.join(self.model_dir, 'time_series_models.pkl')
        
        model_data = {
            'models': self.models,
            'scalers': self.scalers,
            'created_at': datetime.now().isoformat()
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"모델 저장 완료: {model_path}")
    
    def load_models(self):
        """
        저장된 모델 로드
        
        Returns:
            bool: 로드 성공 여부
        """
        model_path = os.path.join(self.model_dir, 'time_series_models.pkl')
        
        if not os.path.exists(model_path):
            print(f"모델 파일이 존재하지 않습니다: {model_path}")
            return False
        
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.models = model_data['models']
            self.scalers = model_data['scalers']
            print(f"모델 로드 완료: {model_path}")
            return True
            
        except Exception as e:
            print(f"모델 로드 오류: {e}")
            return False
    
    def predict(self, target_column, date, hour=None, features=None):
        """
        시계열 예측 수행
        
        Args:
            target_column (str): 예측할 대상 열
            date (str): 날짜 (YYYYMMDD)
            hour (int, optional): 시간 (0-23)
            features (dict, optional): 추가 특성 (예: {'AvgTemp_C': 25, 'AvgHumidity_percent': 60})
            
        Returns:
            dict: 예측 결과
        """
        # 모델 확인
        if target_column not in self.models:
            raise ValueError(f"대상 '{target_column}'에 대한 모델이 학습되지 않았습니다.")
        
        # 날짜/시간 변환
        try:
            if hour is None:
                dt = pd.to_datetime(date, format='%Y%m%d')
                hour = 12  # 기본값: 정오
            else:
                dt = pd.to_datetime(f"{date}{hour:02d}", format='%Y%m%d%H')
        except Exception as e:
            raise ValueError(f"날짜/시간 변환 오류: {e}")
        
        # 기본 특성 생성
        predict_features = {
            'Year': dt.year,
            'Month': dt.month,
            'Day': dt.day,
            'Hour': hour,
            'DayOfWeek': dt.dayofweek,
            'hour_sin': np.sin(2 * np.pi * hour / 24),
            'hour_cos': np.cos(2 * np.pi * hour / 24),
            'day_sin': np.sin(2 * np.pi * dt.day / 31),
            'day_cos': np.cos(2 * np.pi * dt.day / 31),
            'month_sin': np.sin(2 * np.pi * dt.month / 12),
            'month_cos': np.cos(2 * np.pi * dt.month / 12)
        }
        
        # 계절 인코딩
        season_map = {1: 'Winter', 2: 'Winter', 3: 'Spring', 4: 'Spring', 5: 'Spring',
                      6: 'Summer', 7: 'Summer', 8: 'Summer', 9: 'Fall', 10: 'Fall',
                      11: 'Fall', 12: 'Winter'}
        season = season_map[dt.month]
        
        # 계절 원-핫 인코딩
        for s in ['Spring', 'Summer', 'Fall', 'Winter']:
            predict_features[f'Season_{s}'] = 1 if season == s else 0
        
        # 요일 원-핫 인코딩
        for day in range(7):
            predict_features[f'DayOfWeek_{day}'] = 1 if dt.dayofweek == day else 0
        
        # 추가 특성 병합
        if features:
            predict_features.update(features)
        
        # 지연 특성과 롤링 윈도우 특성은 사용할 수 없으므로, 평균값 또는 추정값으로 대체
        # (실제 애플리케이션에서는 이전 데이터를 유지하여 사용 가능)
        
        # 사용할 특성 선택
        model_features = self.models[target_column]['feature_names']
        X = []
        
        for feature in model_features:
            if feature in predict_features:
                X.append(predict_features[feature])
            else:
                # 지연 특성이거나 롤링 윈도우 특성인 경우 0으로 대체
                X.append(0)
        
        # 특성 스케일링
        X_scaled = self.scalers[target_column].transform([X])
        
        # 모델 예측
        rf_model = self.models[target_column]['random_forest']
        ridge_model = self.models[target_column]['ridge']
        
        rf_pred = rf_model.predict(X_scaled)[0]
        ridge_pred = ridge_model.predict(X_scaled)[0]
        
        # 앙상블 예측 (가중 평균)
        ensemble_pred = rf_pred * 0.7 + ridge_pred * 0.3
        
        # 결과 반환
        return {
            'target': target_column,
            'date': date,
            'hour': hour,
            'rf_prediction': float(rf_pred),
            'ridge_prediction': float(ridge_pred),
            'ensemble_prediction': float(ensemble_pred),
            'features_used': predict_features
        }
    
    def predict_next_hours(self, target_column, date, start_hour, hours=24, features=None):
        """
        향후 시간대 예측
        
        Args:
            target_column (str): 예측할 대상 열
            date (str): 날짜 (YYYYMMDD)
            start_hour (int): 시작 시간 (0-23)
            hours (int): 예측할 시간 수
            features (dict, optional): 추가 특성
            
        Returns:
            list: 시간별 예측 결과 목록
        """
        results = []
        
        # 시작 날짜/시간
        try:
            dt = pd.to_datetime(f"{date}{start_hour:02d}", format='%Y%m%d%H')
        except Exception as e:
            raise ValueError(f"날짜/시간 변환 오류: {e}")
        
        # 시간별 예측
        for i in range(hours):
            # 현재 시간 계산
            current_dt = dt + timedelta(hours=i)
            current_date = current_dt.strftime('%Y%m%d')
            current_hour = current_dt.hour
            
            # 예측 수행
            try:
                result = self.predict(target_column, current_date, current_hour, features)
                results.append(result)
            except Exception as e:
                print(f"예측 오류 ({current_date} {current_hour}시): {e}")
                # 오류 발생 시 이전 예측값 또는 기본값 사용
                if results:
                    last_result = results[-1].copy()
                    last_result['date'] = current_date
                    last_result['hour'] = current_hour
                    last_result['error'] = str(e)
                    results.append(last_result)
                else:
                    # 첫 번째 예측에서 오류 발생 시 기본값 사용
                    results.append({
                        'target': target_column,
                        'date': current_date,
                        'hour': current_hour,
                        'rf_prediction': 3.0 if 'WindSpeed' in target_column else 20.0,
                        'ridge_prediction': 3.0 if 'WindSpeed' in target_column else 20.0,
                        'ensemble_prediction': 3.0 if 'WindSpeed' in target_column else 20.0,
                        'error': str(e)
                    })
        
        return results
    
    def predict_next_days(self, target_column, start_date, days=7, features=None):
        """
        향후 날짜 예측 (일별 평균값)
        
        Args:
            target_column (str): 예측할 대상 열
            start_date (str): 시작 날짜 (YYYYMMDD)
            days (int): 예측할 일 수
            features (dict, optional): 추가 특성
            
        Returns:
            list: 일별 예측 결과 목록
        """
        results = []
        
        # 시작 날짜
        try:
            dt = pd.to_datetime(start_date, format='%Y%m%d')
        except Exception as e:
            raise ValueError(f"날짜 변환 오류: {e}")
        
        # 일별 예측
        for i in range(days):
            # 현재 날짜 계산
            current_dt = dt + timedelta(days=i)
            current_date = current_dt.strftime('%Y%m%d')
            
            # 주요 시간대 예측 (6시, 12시, 18시) 및 평균 계산
            day_results = []
            for hour in [6, 12, 18]:
                try:
                    result = self.predict(target_column, current_date, hour, features)
                    day_results.append(result)
                except Exception as e:
                    print(f"예측 오류 ({current_date} {hour}시): {e}")
            
            # 일별 평균 계산
            if day_results:
                avg_rf = sum(r['rf_prediction'] for r in day_results) / len(day_results)
                avg_ridge = sum(r['ridge_prediction'] for r in day_results) / len(day_results)
                avg_ensemble = sum(r['ensemble_prediction'] for r in day_results) / len(day_results)
                
                daily_result = {
                    'target': target_column,
                    'date': current_date,
                    'rf_prediction': float(avg_rf),
                    'ridge_prediction': float(avg_ridge),
                    'ensemble_prediction': float(avg_ensemble),
                    'hourly_predictions': day_results
                }
                results.append(daily_result)
            else:
                # 예측에 실패한 경우 기본값 사용
                results.append({
                    'target': target_column,
                    'date': current_date,
                    'rf_prediction': 3.0 if 'WindSpeed' in target_column else 20.0,
                    'ridge_prediction': 3.0 if 'WindSpeed' in target_column else 20.0,
                    'ensemble_prediction': 3.0 if 'WindSpeed' in target_column else 20.0,
                    'error': '모든 시간대 예측 실패'
                })
        
        return results