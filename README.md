# 전력 발전량 통합 시스템

기상청 API 기반의 풍력/지압 발전량 예측 및 ESS(에너지 저장 시스템) 관리 시스템입니다.

## 개요

이 프로젝트는 인천광역시 미추홀구 용현1.4동의 기상 데이터를 활용하여 특정 위치(5호관-60주년 사이, 인경호 앞, 하이데거숲)의 풍력 및 지압 발전량을 예측하고, ESS를 통해 전력을 효율적으로 관리합니다. 사용자 친화적인 대시보드를 통해 실시간 및 예측 데이터를 시각화하여 제공합니다.

## 주요 기능

### 전력 발전량 예측
- 실시간 풍력 및 지압 발전량 계산
- 일간/주간/월간/연간 발전량 예측
- 위치별 풍속 가중치 적용 (건물 사이 통로 효과 등)
- 시계열 모델을 활용한 기상 데이터 분석

### ESS(에너지 저장 시스템) 관리
- 배터리 셀 충방전 관리 (CC/CV 충전, 방전)
- 전력 생산량에 따른 충방전 속도 자동 조절
- SOC(State of Charge) 모니터링
- 일간 ESS 운영 스케줄 자동 생성
- ESS 시뮬레이션 기능

### 사용자 인터페이스
- 전력 대시보드: 실시간/일간/주간/월간/연간 발전량 시각화
- ESS 대시보드: 배터리 상태/실시간 ESS/일간 스케줄/시뮬레이션 결과 시각화
- 반응형 웹 디자인

## 기술 스택

### 백엔드
- Python 3.10
- FastAPI: RESTful API 프레임워크
- NumPy/Pandas: 데이터 처리
- Scikit-learn: 시계열 분석 및 예측 모델
- 기상청 API 연동

### 프론트엔드
- React.js: UI 프레임워크
- Recharts: 데이터 시각화
- Tailwind CSS: 스타일링

### 인프라
- Docker & Docker Compose: 컨테이너화
- Nginx: 프론트엔드 웹 서버

## 설치 및 실행 방법

### 사전 요구사항
- Docker 및 Docker Compose 설치
- 기상청 API 서비스 키 (KMA_SERVICE_KEY)

### 설치 단계

1. 저장소 클론

2. 환경 변수 설정
   ```bash
   # backend/.env 파일 생성
   KMA_API_URL=https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0
   KMA_SERVICE_KEY=<your-service-key>
   FORECAST_NX=54
   FORECAST_NY=124
   UPLOAD_DIR=../uploads
   MODEL_DIR=../models
   CACHE_DIR=../cache
   
   # frontend/.env 파일 생성
   REACT_APP_KMA_API_URL=https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0
   REACT_APP_KMA_SERVICE_KEY=<your-service-key>
   REACT_APP_API_BASE_URL=http://localhost:8000/api
   REACT_APP_FORECAST_NX=54
   REACT_APP_FORECAST_NY=124
   ```

3. Docker Compose로 실행
   ```bash
   docker-compose up -d
   ```

4. 웹 브라우저에서 접속
   ```
   http://localhost:3000
   ```

## 시스템 구조

```
├── backend/                     # 백엔드 코드
│   ├── app.py                   # FastAPI 메인 앱
│   ├── power_calculation.py     # 전력 계산 모듈
│   ├── power_router.py          # 전력 관련 API 라우터
│   ├── weather_router.py        # 날씨 관련 API 라우터
│   ├── time_series_analysis.py  # 시계열 분석 모듈
│   ├── ess_controller.py        # ESS 제어 모듈
│   └── ess_router.py            # ESS 관련 API 라우터
│
├── frontend/                    # 프론트엔드 코드
│   ├── src/
│   │   ├── App.js               # 메인 앱 컴포넌트
│   │   ├── PowerDashboard.js    # 전력 대시보드 컴포넌트
│   │   └── ESSDashboard.js      # ESS 대시보드 컴포넌트
│
├── data/                        # 데이터 디렉토리
├── models/                      # 모델 디렉토리
├── uploads/                     # 업로드 디렉토리
├── cache/                       # 캐시 디렉토리
├── logs/                        # 로그 디렉토리
│
└── docker-compose.yml           # Docker Compose 설정
```

## API 엔드포인트

### 전력 관련 API

| 엔드포인트 | 메소드 | 설명 |
|------------|--------|------|
| `/api/power/` | GET | 전력 API 정보 |
| `/api/power/predict` | POST | 시간당 발전량 예측 |
| `/api/power/realtime/{location}` | GET | 실시간 발전량 예측 |
| `/api/power/daily/{location}` | GET | 일일 발전량 예측 |
| `/api/power/weekly/{location}` | GET | 주간 발전량 예측 |
| `/api/power/monthly/{location}` | GET | 월간 발전량 예측 |
| `/api/power/annual/{location}` | GET | 연간 발전량 예측 |

### 날씨 관련 API

| 엔드포인트 | 메소드 | 설명 |
|------------|--------|------|
| `/api/weather/current` | GET | 현재 날씨 조회 |
| `/api/weather/forecast/short` | GET | 단기예보 조회 |
| `/api/weather/min-max-temperatures` | GET | 최저/최고 기온 조회 |
| `/api/weather/wind-factors` | GET | 위치별 풍속 가중치 조회 |
| `/api/weather/location-wind-speeds` | GET | 위치별 풍속 정보 조회 |

### ESS 관련 API

| 엔드포인트 | 메소드 | 설명 |
|------------|--------|------|
| `/api/ess/` | GET | ESS 시스템 정보 |
| `/api/ess/battery/status` | GET | 배터리 상태 조회 |
| `/api/ess/battery/charge` | POST | 배터리 충전 시작 |
| `/api/ess/battery/discharge` | POST | 배터리 방전 시작 |
| `/api/ess/simulate/day` | POST | 일간 ESS 운영 시뮬레이션 |
| `/api/ess/realtime/{location}` | GET | 실시간 ESS 운영 상태 조회 |
| `/api/ess/daily-schedule/{location}` | GET | 일간 ESS 운영 스케줄 생성 |

## ESS 알고리즘 상세 설명

### 셀 충전 Sequence (CC/CV 충전)
- **Step 0:** 전류 크기 변환 (0.1C mA)
- **Step 1:** 0.1C mA CC 충전 (Cut off 조건: 전압 >= 4.2V)
- **Step 2:** 4.2V CV 충전 (Cut off 조건: 전류 <= 0.02C mA)
- **Step 3:** 휴식 (Cut off 조건: 120분)

### 셀 방전 Sequence
- **Step 1:** 0.0833C mA CC 방전 (가로등 가동시간에 따라 조정)
- **Step 2:** 휴식 (Cut off 조건: 120분) - ESS cell
- **Step 2-1:** CC에 대한 전압 변환 장치를 통해 필요한 전압으로 변환

### 전력 생산량에 따른 C-rate 조정
- **생산량 > 25804.8 Wh일 경우:**
  - **충전:** 0.1 x [0.1 / { (6.75 x 10^(-9)) x A + 0.1 }] CC 충전
  - **방전:** 0.0833 x [{ (6.75 x 10^(-9)) x A + 0.0833 } / 0.0833] CC 방전
- **생산량 < 25804.8 Wh일 경우:**
  - 기존 충방전 메커니즘 실행
  - SOC >= 100% (OCV >= 4.2V)되는 순간 Cut off

## 사용자 인터페이스 안내

### 전력 대시보드
1. **실시간 발전량:** 현재 풍력/지압 발전량 및 충족률
2. **일일 발전량:** 24시간 동안의 시간별 발전량
3. **주간 발전량:** 7일간의 일별 발전량
4. **월간 발전량:** 4주간의 주별 발전량
5. **연간 발전량:** 12개월의 월별 발전량

### ESS 대시보드
1. **배터리 상태:** SOC, 전압, 충방전 상태 모니터링
2. **실시간 ESS:** 실시간 충방전 상태 및 제어 정보
3. **일간 스케줄:** 24시간 동안의 ESS 운영 계획
4. **ESS 시뮬레이션:** 하루 동안의 ESS 운영 시뮬레이션 결과

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

## 연락처

프로젝트 관련 문의는 [이메일 주소]로 연락주세요.