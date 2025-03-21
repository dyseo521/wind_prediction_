// src/EnhancedDashboard.js
import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, RadialBarChart, RadialBar,
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Label, ReferenceLine 
} from 'recharts';
import inhaLogo from './images/inha.jpg';

// 환경변수 접근 방식
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

// 현대적인 색상 팔레트
const COLORS = {
  primary: '#1a4d8c',       // 인하 블루
  secondary: '#1cb9a7',     // 티얼 색상
  accent: '#ff7e47',        // 오렌지 색상
  warning: '#ffa600',       // 주황색 경고
  success: '#2ec88e',       // 초록색 성공
  danger: '#ff5e5b',        // 빨간색 위험
  neutral: {
    100: '#f8f9fa',
    200: '#e9ecef',
    300: '#dee2e6',
    400: '#ced4da',
    500: '#adb5bd',
    600: '#6c757d',
    700: '#495057',
    800: '#343a40',
    900: '#212529'
  },
  charts: {
    wind: '#4361ee',
    piezo: '#3dd5f3',
    solar: '#4cc9f0',
    total: '#1a4d8c',
    consumption: '#ff7e47',
    battery: '#2ec88e',
    background: 'rgba(240, 244, 248, 0.7)'
  }
};

const EnhancedDashboard = () => {
  // 기본 상태 관리
  const [view, setView] = useState('overview');
  const [selectedLocation, setSelectedLocation] = useState('5호관_60주년_사이');
  const [period, setPeriod] = useState('realtime');
  const [showSidebar, setShowSidebar] = useState(true);
  const [windSpeed, setWindSpeed] = useState(3.5);
  const [theme, setTheme] = useState('light');
  const [isLoading, setIsLoading] = useState(false);
  
  // 데이터 상태 관리 (기존 대시보드에서 통합)
  const [realtimePower, setRealtimePower] = useState(null);
  const [dailyPower, setDailyPower] = useState(null);
  const [weeklyPower, setWeeklyPower] = useState(null);
  const [monthlyPower, setMonthlyPower] = useState(null);
  const [annualPower, setAnnualPower] = useState(null);
  const [batteryStatus, setBatteryStatus] = useState(null);
  const [realtimeStatus, setRealtimeStatus] = useState(null);
  const [dailySchedule, setDailySchedule] = useState(null);
  const [simulationResult, setSimulationResult] = useState(null);
  const [error, setError] = useState(null);
  
  // 위치 옵션
  const locationOptions = [
    { value: '5호관_60주년_사이', label: '5호관-60주년 사이' },
    { value: '인경호_앞', label: '인경호 앞' },
    { value: '하이데거숲', label: '하이데거숲' }
  ];

  // API 호출 함수 (기존 대시보드에서 통합)
  const fetchData = async (endpoint) => {
    try {
      const response = await fetch(endpoint);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API 호출 오류:', error);
      throw error;
    }
  };

  // 실시간 전력 데이터 조회
  const fetchRealtimePower = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await fetchData(`${API_BASE_URL}/power/realtime/${selectedLocation}`);
      setRealtimePower(data);
    } catch (err) {
      console.error('실시간 전력 데이터 조회 오류:', err);
      setError(err.message || '실시간 전력 데이터 조회 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 일일 전력 데이터 조회
  const fetchDailyPower = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await fetchData(`${API_BASE_URL}/power/daily/${selectedLocation}?avg_wind_speed=${windSpeed}`);
      setDailyPower(data);
    } catch (err) {
      console.error('일일 전력 데이터 조회 오류:', err);
      setError(err.message || '일일 전력 데이터 조회 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 주간 전력 데이터 조회
  const fetchWeeklyPower = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await fetchData(`${API_BASE_URL}/power/weekly/${selectedLocation}?avg_wind_speed=${windSpeed}`);
      setWeeklyPower(data);
    } catch (err) {
      console.error('주간 전력 데이터 조회 오류:', err);
      setError(err.message || '주간 전력 데이터 조회 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 월간 전력 데이터 조회
  const fetchMonthlyPower = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await fetchData(`${API_BASE_URL}/power/monthly/${selectedLocation}?avg_wind_speed=${windSpeed}&min_temp=5&max_temp=25`);
      setMonthlyPower(data);
    } catch (err) {
      console.error('월간 전력 데이터 조회 오류:', err);
      setError(err.message || '월간 전력 데이터 조회 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 연간 전력 데이터 조회
  const fetchAnnualPower = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await fetchData(`${API_BASE_URL}/power/annual/${selectedLocation}`);
      setAnnualPower(data);
    } catch (err) {
      console.error('연간 전력 데이터 조회 오류:', err);
      setError(err.message || '연간 전력 데이터 조회 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 배터리 상태 조회
  const fetchBatteryStatus = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await fetchData(`${API_BASE_URL}/ess/battery/status`);
      setBatteryStatus(data);
    } catch (err) {
      console.error('배터리 상태 조회 오류:', err);
      setError(err.message || '배터리 상태 조회 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 실시간 ESS 상태 조회
  const fetchRealtimeStatus = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await fetchData(`${API_BASE_URL}/ess/realtime/${selectedLocation}`);
      setRealtimeStatus(data);
    } catch (err) {
      console.error('실시간 ESS 상태 조회 오류:', err);
      setError(err.message || '실시간 ESS 상태 조회 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 일간 ESS 스케줄 조회
  const fetchDailySchedule = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await fetchData(`${API_BASE_URL}/ess/daily-schedule/${selectedLocation}?avg_wind_speed=${windSpeed}`);
      setDailySchedule(data);
    } catch (err) {
      console.error('일간 ESS 스케줄 조회 오류:', err);
      setError(err.message || '일간 ESS 스케줄 조회 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // ESS 시뮬레이션 실행
  const runEssSimulation = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const today = new Date().toISOString().split('T')[0].replace(/-/g, '');
      
      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location: selectedLocation,
          date: today,
          avg_wind_speed: windSpeed,
          start_hour: 6,
          end_hour: 18
        })
      };
      
      const response = await fetch(`${API_BASE_URL}/ess/simulate/day`, requestOptions);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      const data = await response.json();
      setSimulationResult(data);
    } catch (err) {
      console.error('ESS 시뮬레이션 오류:', err);
      setError(err.message || 'ESS 시뮬레이션 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 배터리 충전 요청
  const startBatteryCharging = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // 현재 전력 생산량 가져오기
      let powerProduction = 1000; // 기본값
      if (realtimeStatus && realtimeStatus.power_production) {
        powerProduction = realtimeStatus.power_production;
      }
      
      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          power_production: powerProduction,
          location: selectedLocation
        })
      };
      
      const response = await fetch(`${API_BASE_URL}/ess/battery/charge`, requestOptions);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      const data = await response.json();
      alert('충전 요청 성공: ' + JSON.stringify(data));
      
      // 배터리 상태 새로고침
      fetchBatteryStatus();
    } catch (err) {
      console.error('배터리 충전 요청 오류:', err);
      setError(err.message || '배터리 충전 요청 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 배터리 방전 요청
  const startBatteryDischarging = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location: selectedLocation,
          is_nighttime: true
        })
      };
      
      const response = await fetch(`${API_BASE_URL}/ess/battery/discharge`, requestOptions);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      const data = await response.json();
      alert('방전 요청 성공: ' + JSON.stringify(data));
      
      // 배터리 상태 새로고침
      fetchBatteryStatus();
    } catch (err) {
      console.error('배터리 방전 요청 오류:', err);
      setError(err.message || '배터리 방전 요청 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 데이터 새로고침
  const refreshData = () => {
    setIsLoading(true);
    
    if (view === 'overview') {
      Promise.all([fetchRealtimePower(), fetchBatteryStatus()])
        .finally(() => setIsLoading(false));
    } 
    else if (view === 'power') {
      if (period === 'realtime') fetchRealtimePower();
      else if (period === 'daily') fetchDailyPower();
      else if (period === 'weekly') fetchWeeklyPower();
      else if (period === 'monthly') fetchMonthlyPower();
      else if (period === 'annual') fetchAnnualPower();
    } 
    else if (view === 'battery') {
      Promise.all([fetchBatteryStatus(), fetchRealtimeStatus()])
        .finally(() => setIsLoading(false));
    } 
    else if (view === 'analytics') {
      Promise.all([fetchRealtimePower(), fetchWeeklyPower(), fetchMonthlyPower(), fetchAnnualPower()])
        .finally(() => setIsLoading(false));
    }
  };

  // 위치나 탭 변경 시 데이터 새로고침
  useEffect(() => {
    refreshData();
    
    // 실시간 상태 탭에서는 30초마다 자동 새로고침
    let intervalId = null;
    if ((view === 'overview' || (view === 'power' && period === 'realtime') || view === 'battery')) {
      intervalId = setInterval(() => {
        refreshData();
      }, 30000);
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [selectedLocation, view, period, windSpeed]);

  // 유틸리티 함수들
  // 배터리 상태 색상 결정
  const getBatteryStateColor = (state) => {
    if (state === 'CHARGING_CC' || state === 'CHARGING_CV' || state === 'CHARGING') return COLORS.charts.battery;
    if (state === 'DISCHARGING') return COLORS.charts.wind;
    if (state === 'REST') return COLORS.warning;
    return COLORS.neutral[500];
  };

  // SOC 색상 결정
  const getSocColor = (soc) => {
    if (soc >= 70) return COLORS.charts.battery;
    if (soc >= 30) return COLORS.warning;
    return COLORS.danger;
  };

  // 시간 포맷 변환
  const formatHour = (hour) => {
    return `${hour}:00`;
  };

  // 단위 포맷 변환 (Wh → kWh, 필요한 경우)
  const formatEnergy = (energy, unit = 'Wh') => {
    if (!energy && energy !== 0) return '0 ' + unit;
    
    if (unit === 'Wh' && energy >= 1000) {
      return `${(energy / 1000).toFixed(2)} kWh`;
    }
    return `${energy.toFixed(2)} ${unit}`;
  };

  // Dashboard Header Component
  const DashboardHeader = () => (
    <header className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
      <div className="flex items-center">
        <img
          src={inhaLogo}
          alt="인하대학교 로고"
          className="w-10 h-10 mr-3"
        />
        <div>
          <h1 className="text-2xl font-bold text-neutral-800 dark:text-white tracking-tight">
            전력 발전량 대시보드
          </h1>
          <p className="text-sm text-neutral-600 dark:text-neutral-300">
            인하대학교 풍력 및 지압 발전 시스템 통합 모니터링
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center bg-white dark:bg-neutral-800 rounded-lg shadow-sm px-3 py-1">
          <span className="text-xs text-neutral-500 dark:text-neutral-400 mr-2">
            위치:
          </span>
          <select
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
            className="text-sm bg-transparent border-none focus:ring-0 text-neutral-800 dark:text-white"
          >
            {locationOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {view === 'power' && (
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="text-sm bg-white dark:bg-neutral-800 rounded-lg shadow-sm px-3 py-1 border-none focus:ring-0 text-neutral-800 dark:text-white"
          >
            <option value="realtime">실시간</option>
            <option value="daily">일간</option>
            <option value="weekly">주간</option>
            <option value="monthly">월간</option>
            <option value="annual">연간</option>
          </select>
        )}

        <button
          onClick={refreshData}
          className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-white hover:bg-opacity-90 transition-colors"
          disabled={isLoading}
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" 
            />
          </svg>
        </button>

        <button
          onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
          className="flex items-center justify-center w-8 h-8 rounded-full bg-white dark:bg-neutral-800 text-neutral-700 dark:text-white shadow-sm hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors"
        >
          {theme === 'light' ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          )}
        </button>
      </div>
    </header>
  );

  // Sidebar Navigation Component
  const SidebarNavigation = () => (
    <div className={`fixed left-0 top-0 h-full bg-white dark:bg-neutral-900 shadow-lg z-20 transition-all duration-300 ${showSidebar ? 'w-64' : 'w-16'} pt-20`}>
      <button 
        onClick={() => setShowSidebar(!showSidebar)}
        className="absolute top-6 right-4 w-8 h-8 flex items-center justify-center text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-white"
      >
        {showSidebar ? (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
          </svg>
        )}
      </button>

      <nav className="px-2 py-4">
        {[
          { id: 'overview', label: '개요', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
          { id: 'power', label: '발전량', icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
          { id: 'battery', label: '배터리', icon: 'M4 4v7l5 5 5-5v-7a1 1 0 00-1-1H5a1 1 0 00-1 1zm9 12v4h6v-8h-3v4h-3zm-9 0v4h6v-8H7v4H4z' },
          { id: 'analytics', label: '통계', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
          { id: 'settings', label: '설정', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' },
        ].map((item) => (
          <button
            key={item.id}
            onClick={() => setView(item.id)}
            className={`flex items-center w-full p-3 mb-1 rounded-lg transition-colors ${
              view === item.id
                ? 'bg-primary text-white'
                : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800'
            }`}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d={item.icon}
              />
            </svg>
            {showSidebar && <span className="ml-3 text-sm font-medium">{item.label}</span>}
          </button>
        ))}
      </nav>

      <div className={`absolute bottom-8 left-0 right-0 px-4 ${!showSidebar && 'hidden'}`}>
        <div className="bg-neutral-100 dark:bg-neutral-800 rounded-lg p-3">
          <div className="text-xs text-neutral-500 dark:text-neutral-400 mb-2">풍속 조절</div>
          <div className="flex items-center">
            <input
              type="range"
              min="0.5"
              max="10"
              step="0.1"
              value={windSpeed}
              onChange={(e) => setWindSpeed(parseFloat(e.target.value))}
              className="w-full h-1 bg-neutral-300 dark:bg-neutral-700 rounded-lg appearance-none"
            />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-xs text-neutral-500 dark:text-neutral-400">0.5 m/s</span>
            <span className="text-xs font-medium text-primary dark:text-blue-400">{windSpeed} m/s</span>
            <span className="text-xs text-neutral-500 dark:text-neutral-400">10 m/s</span>
          </div>
        </div>
      </div>
    </div>
  );

  // Status Card Component
  const StatusCard = ({ title, value, unit, icon, color, change, isIncreasing }) => (
    <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4 relative">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-1">{title}</p>
          <div className="flex items-baseline">
            <p className="text-2xl font-bold text-neutral-900 dark:text-white">{value}</p>
            {unit && <span className="text-sm ml-1 text-neutral-500 dark:text-neutral-400">{unit}</span>}
          </div>
          {change && (
            <div className={`flex items-center mt-1 text-xs ${isIncreasing ? 'text-success' : 'text-danger'}`}>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-3 w-3 mr-1"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d={isIncreasing ? 'M5 15l7-7 7 7' : 'M19 9l-7 7-7-7'}
                />
              </svg>
              {change}%
            </div>
          )}
        </div>
        <div className={`flex items-center justify-center w-9 h-9 rounded-full bg-${color}-100 dark:bg-${color}-900 bg-opacity-80`}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className={`h-5 w-5 text-${color}-600 dark:text-${color}-400`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={icon} />
          </svg>
        </div>
      </div>
    </div>
  );

  // 로딩 컴포넌트
  const LoadingOverlay = () => (
    isLoading && (
      <div className="fixed inset-0 bg-black bg-opacity-30 z-50 flex items-center justify-center">
        <div className="bg-white dark:bg-neutral-800 rounded-xl p-6 flex flex-col items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mb-4"></div>
          <p className="text-neutral-800 dark:text-white">데이터를 로딩 중입니다...</p>
        </div>
      </div>
    )
  );

  // 오류 표시 컴포넌트
  const ErrorDisplay = () => (
    error && (
      <div className="mb-6 p-4 bg-red-100 text-red-700 rounded-xl shadow-sm">
        <p className="font-semibold">오류 발생:</p>
        <p>{error}</p>
      </div>
    )
  );

  // Quick Stats Component for Overview
  const QuickStats = () => {
    // 실제 데이터 또는 기본값 사용
    const windPower = realtimePower?.wind_power_wh || 0;
    const piezoPower = realtimePower?.piezo_power_wh || 0;
    const totalPower = realtimePower?.total_power_wh || 0;
    const sufficiencyPercentage = realtimePower?.sufficiency_percentage || 0;
    const batteryLevel = batteryStatus?.soc || 0;

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatusCard
          title="풍력 발전량"
          value={windPower.toFixed(2)}
          unit="Wh"
          icon="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z"
          color="blue"
        />
        <StatusCard
          title="지압 발전량"
          value={piezoPower.toFixed(2)}
          unit="Wh"
          icon="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
          color="green"
        />
        <StatusCard
          title="충족률"
          value={sufficiencyPercentage.toFixed(1)}
          unit="%"
          icon="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          color="amber"
        />
        <StatusCard
          title="배터리 상태"
          value={batteryLevel}
          unit="%"
          icon="M13 10V3L4 14h7v7l9-11h-7z"
          color="indigo"
        />
      </div>
    );
  };

  // Weather Conditions Component
  const WeatherConditions = () => {
    // 실제 데이터 또는 기본값 사용
    const windSpeed = realtimePower?.weather?.windSpeed || 0;
    const temperature = realtimePower?.weather?.temperature || 0;
    const humidity = realtimePower?.weather?.humidity || 0;
    const peopleCount = realtimePower?.people_count || 0;

    return (
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4 mb-6">
        <h3 className="text-sm font-medium text-neutral-800 dark:text-white mb-3">날씨 조건</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex items-center">
            <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center mr-3">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4 text-blue-600 dark:text-blue-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"
                />
              </svg>
            </div>
            <div>
              <p className="text-xs text-neutral-500 dark:text-neutral-400">풍속</p>
              <p className="text-sm font-medium text-neutral-900 dark:text-white">{windSpeed} m/s</p>
            </div>
          </div>
          <div className="flex items-center">
            <div className="w-8 h-8 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center mr-3">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4 text-red-600 dark:text-red-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16.5l1.5 2h7l1.5-2m3-11.5l-3 10.5H7L4 5"
                />
              </svg>
            </div>
            <div>
              <p className="text-xs text-neutral-500 dark:text-neutral-400">기온</p>
              <p className="text-sm font-medium text-neutral-900 dark:text-white">{temperature}°C</p>
            </div>
          </div>
          <div className="flex items-center">
            <div className="w-8 h-8 rounded-full bg-teal-100 dark:bg-teal-900 flex items-center justify-center mr-3">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4 text-teal-600 dark:text-teal-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
            </div>
            <div>
              <p className="text-xs text-neutral-500 dark:text-neutral-400">습도</p>
              <p className="text-sm font-medium text-neutral-900 dark:text-white">{humidity}%</p>
            </div>
          </div>
          <div className="flex items-center">
            <div className="w-8 h-8 rounded-full bg-violet-100 dark:bg-violet-900 flex items-center justify-center mr-3">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4 text-violet-600 dark:text-violet-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
            </div>
            <div>
              <p className="text-xs text-neutral-500 dark:text-neutral-400">인원 수</p>
              <p className="text-sm font-medium text-neutral-900 dark:text-white">{peopleCount} 명</p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Overview Dashboard
  const OverviewDashboard = () => {
    // 데이터 준비
    const dailyData = dailyPower?.hourly_results?.map(hour => ({
      hour: hour.hour,
      label: formatHour(hour.hour),
      wind: hour.wind_power_wh,
      piezo: hour.piezo_power_wh,
      total: hour.total_power_wh
    })) || [];

    const pieData = [
      { name: '풍력', value: realtimePower?.wind_power_wh || 0 },
      { name: '지압', value: realtimePower?.piezo_power_wh || 0 }
    ];

    const renweablePercentage = realtimePower?.wind_power_wh && realtimePower?.total_power_wh
      ? ((realtimePower.wind_power_wh / realtimePower.total_power_wh) * 100).toFixed(1)
      : 0;

    const weeklyData = weeklyPower?.daily_results?.map(day => ({
      day: new Date(day.date).toLocaleDateString('ko-KR', { weekday: 'short' }),
      wind: day.daily_wind_power_wh,
      piezo: day.daily_piezo_power_wh,
      total: day.daily_total_power_wh
    })) || [];

    return (
      <>
        <QuickStats />
        <WeatherConditions />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4 h-full">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-medium text-neutral-800 dark:text-white">시간별 발전량</h3>
                <div className="flex space-x-2">
                  <button className="text-xs px-2 py-1 rounded bg-primary bg-opacity-10 text-primary">오늘</button>
                  <button className="text-xs px-2 py-1 rounded text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-700">이번주</button>
                  <button className="text-xs px-2 py-1 rounded text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-700">이번달</button>
                </div>
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={dailyData}>
                    <defs>
                      <linearGradient id="colorWind" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={COLORS.charts.wind} stopOpacity={0.8} />
                        <stop offset="95%" stopColor={COLORS.charts.wind} stopOpacity={0.1} />
                      </linearGradient>
                      <linearGradient id="colorPiezo" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={COLORS.charts.piezo} stopOpacity={0.8} />
                        <stop offset="95%" stopColor={COLORS.charts.piezo} stopOpacity={0.1} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis 
                      dataKey="label" 
                      tick={{ fontSize: 12 }} 
                      tickLine={false}
                      axisLine={{ stroke: '#E0E0E0' }}
                    />
                    <YAxis 
                      tick={{ fontSize: 12 }} 
                      tickLine={false}
                      axisLine={{ stroke: '#E0E0E0' }}
                    />
                    <Tooltip
                      contentStyle={{ 
                        backgroundColor: 'rgba(255, 255, 255, 0.9)', 
                        borderRadius: '8px',
                        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
                        border: 'none'
                      }}
                    />
                    <Legend iconType="circle" />
                    <Area 
                      type="monotone" 
                      dataKey="wind" 
                      name="풍력" 
                      stroke={COLORS.charts.wind} 
                      fillOpacity={1} 
                      fill="url(#colorWind)" 
                    />
                    <Area 
                      type="monotone" 
                      dataKey="piezo" 
                      name="지압" 
                      stroke={COLORS.charts.piezo} 
                      fillOpacity={1} 
                      fill="url(#colorPiezo)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div>
            <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4 h-full">
              <h3 className="text-sm font-medium text-neutral-800 dark:text-white mb-4">발전 에너지 구성</h3>
              <div className="h-60 flex flex-col justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {pieData.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={index === 0 ? COLORS.charts.wind : COLORS.charts.piezo} 
                        />
                      ))}
                    </Pie>
                    <Tooltip 
                      formatter={(value) => [`${value.toFixed(2)} Wh`, '발전량']}
                      contentStyle={{ 
                        backgroundColor: 'rgba(255, 255, 255, 0.9)', 
                        borderRadius: '8px',
                        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
                        border: 'none'
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="bg-neutral-50 dark:bg-neutral-900 p-3 rounded-lg">
                  <div className="flex items-center">
                    <div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>
                    <span className="text-xs text-neutral-600 dark:text-neutral-300">풍력</span>
                  </div>
                  <p className="text-lg font-semibold text-neutral-900 dark:text-white mt-1">
                    {renweablePercentage}%
                  </p>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
                    {realtimePower?.wind_power_wh?.toFixed(2) || 0} Wh
                  </p>
                </div>
                <div className="bg-neutral-50 dark:bg-neutral-900 p-3 rounded-lg">
                  <div className="flex items-center">
                    <div className="w-3 h-3 rounded-full bg-cyan-400 mr-2"></div>
                    <span className="text-xs text-neutral-600 dark:text-neutral-300">지압</span>
                  </div>
                  <p className="text-lg font-semibold text-neutral-900 dark:text-white mt-1">
                    {(100 - renweablePercentage).toFixed(1)}%
                  </p>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
                    {realtimePower?.piezo_power_wh?.toFixed(2) || 0} Wh
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4">
            <h3 className="text-sm font-medium text-neutral-800 dark:text-white mb-4">ESS 배터리 상태</h3>
            <div className="flex space-x-8">
              <div className="relative w-32 h-32">
                <svg className="w-32 h-32" viewBox="0 0 36 36">
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#E5E7EB"
                    strokeWidth="2"
                    className="dark:stroke-neutral-700"
                  />
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke={COLORS.secondary}
                    strokeWidth="2"
                    strokeDasharray={`${batteryStatus?.soc || 0}, 100`}
                    className="dark:stroke-teal-500"
                  />
                  <text x="18" y="20.5" textAnchor="middle" className="text-2xl font-bold fill-neutral-800 dark:fill-white">
                    {batteryStatus?.soc || 0}%
                  </text>
                </svg>
              </div>
              <div className="flex-1">
                <div className="grid grid-cols-2 gap-y-4">
                  <div>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400">상태</p>
                    <p className="text-sm font-medium text-neutral-900 dark:text-white">{batteryStatus?.state || '-'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400">전압</p>
                    <p className="text-sm font-medium text-neutral-900 dark:text-white">{batteryStatus?.voltage || 0}V</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400">온도</p>
                    <p className="text-sm font-medium text-neutral-900 dark:text-white">{batteryStatus?.temperature || 0}K</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400">용량</p>
                    <p className="text-sm font-medium text-neutral-900 dark:text-white">{batteryStatus?.capacity || 0}Ah</p>
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-2">
                  <button 
                    onClick={startBatteryCharging}
                    className="text-xs font-medium px-3 py-2 rounded-lg bg-green-100 text-green-700 hover:bg-green-200 transition-colors dark:bg-green-900 dark:text-green-300 dark:hover:bg-green-800"
                  >
                    충전 시작
                  </button>
                  <button 
                    onClick={startBatteryDischarging}
                    className="text-xs font-medium px-3 py-2 rounded-lg bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800"
                  >
                    방전 시작
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4">
            <h3 className="text-sm font-medium text-neutral-800 dark:text-white mb-4">주간 발전량 추이</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={weeklyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                  <XAxis 
                    dataKey="day" 
                    tick={{ fontSize: 12 }} 
                    tickLine={false}
                    axisLine={{ stroke: '#E0E0E0' }}
                  />
                  <YAxis 
                    tick={{ fontSize: 12 }} 
                    tickLine={false}
                    axisLine={{ stroke: '#E0E0E0' }}
                  />
                  <Tooltip
                    contentStyle={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.9)', 
                      borderRadius: '8px',
                      boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
                      border: 'none'
                    }}
                  />
                  <Legend iconType="circle" />
                  <Bar dataKey="wind" name="풍력" fill={COLORS.charts.wind} radius={[4, 4, 0, 0]} />
                  <Bar dataKey="piezo" name="지압" fill={COLORS.charts.piezo} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </>
    );
  };

  // Power Dashboard
  const PowerDashboard = () => {
    // 각 기간별 데이터 준비
    let chartData;
    let pieData;
    let compareData;
    let chartTitle;
    
    switch (period) {
      case 'realtime':
        chartData = dailyPower?.hourly_results?.map(hour => ({
          hour: hour.hour,
          label: formatHour(hour.hour),
          total: hour.total_power_wh
        })) || [];
        
        pieData = [
          { name: '풍력', value: realtimePower?.wind_power_wh || 0 },
          { name: '지압', value: realtimePower?.piezo_power_wh || 0 }
        ];
        
        compareData = [
          { name: '발전량', value: realtimePower?.total_power_wh || 0 },
          { name: '소비량', value: realtimePower?.streetlight_consumption_wh || 0 }
        ];
        
        chartTitle = '실시간 발전량';
        break;
        
      case 'daily':
        chartData = dailyPower?.hourly_results?.map(hour => ({
          hour: hour.hour,
          label: formatHour(hour.hour),
          total: hour.total_power_wh
        })) || [];
        
        pieData = [
          { name: '풍력', value: dailyPower?.daily_wind_power_wh || 0 },
          { name: '지압', value: dailyPower?.daily_piezo_power_wh || 0 }
        ];
        
        compareData = [
          { name: '발전량', value: dailyPower?.daily_total_power_wh || 0 },
          { name: '소비량', value: dailyPower?.streetlight_consumption_wh || 0 }
        ];
        
        chartTitle = '일간 발전량';
        break;
        
      case 'weekly':
        chartData = weeklyPower?.daily_results?.map(day => ({
          label: new Date(day.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
          total: day.daily_total_power_wh
        })) || [];
        
        pieData = [
          { name: '풍력', value: weeklyPower?.weekly_wind_power_wh || 0 },
          { name: '지압', value: weeklyPower?.weekly_piezo_power_wh || 0 }
        ];
        
        compareData = [
          { name: '발전량', value: weeklyPower?.weekly_total_power_wh || 0 },
          { name: '소비량', value: weeklyPower?.streetlight_consumption_wh || 0 }
        ];
        
        chartTitle = '주간 발전량';
        break;
        
      case 'monthly':
        chartData = monthlyPower?.weekly_results?.map((week, index) => ({
          label: `Week ${index + 1}`,
          total: week.weekly_total_power_wh
        })) || [];
        
        pieData = [
          { name: '풍력', value: monthlyPower?.monthly_wind_power_wh || 0 },
          { name: '지압', value: monthlyPower?.monthly_piezo_power_wh || 0 }
        ];
        
        compareData = [
          { name: '발전량', value: monthlyPower?.monthly_total_power_wh || 0 },
          { name: '소비량', value: monthlyPower?.streetlight_consumption_wh || 0 }
        ];
        
        chartTitle = '월간 발전량';
        break;
        
      case 'annual':
        chartData = annualPower?.monthly_results?.map(month => ({
          label: month.month,
          total: month.monthly_total_power_wh
        })) || [];
        
        pieData = [
          { name: '풍력', value: annualPower?.annual_wind_power_wh || 0 },
          { name: '지압', value: annualPower?.annual_piezo_power_wh || 0 }
        ];
        
        compareData = [
          { name: '발전량', value: annualPower?.annual_total_power_wh || 0 },
          { name: '소비량', value: annualPower?.streetlight_consumption_wh || 0 }
        ];
        
        chartTitle = '연간 발전량';
        break;
        
      default:
        chartData = [];
        pieData = [];
        compareData = [];
        chartTitle = '발전량';
    }

    // 전력 과부족 계산
    const powerSurplus = (compareData[0]?.value || 0) - (compareData[1]?.value || 0);
    const isSufficient = powerSurplus >= 0;

    return (
      <div className="space-y-6">
        <QuickStats />

        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-medium text-neutral-800 dark:text-white">{chartTitle}</h3>
            <div className="flex items-center space-x-2">
              <button className="text-xs px-2 py-1 rounded text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-700">
                CSV 내보내기
              </button>
              <button className="text-xs px-2 py-1 rounded text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-700">
                상세 보기
              </button>
            </div>
          </div>
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={COLORS.charts.total} stopOpacity={0.8} />
                    <stop offset="95%" stopColor={COLORS.charts.total} stopOpacity={0.1} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  dataKey="label" 
                  tick={{ fontSize: 12 }} 
                  tickLine={false}
                  axisLine={{ stroke: '#E0E0E0' }}
                />
                <YAxis 
                  tick={{ fontSize: 12 }} 
                  tickLine={false}
                  axisLine={{ stroke: '#E0E0E0' }}
                />
                <Tooltip
                  contentStyle={{ 
                    backgroundColor: 'rgba(255, 255, 255, 0.9)', 
                    borderRadius: '8px',
                    boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
                    border: 'none'
                  }}
                  formatter={(value) => [`${value.toFixed(2)} Wh`, '발전량']}
                />
                <Legend iconType="circle" />
                <Area 
                  type="monotone" 
                  dataKey="total" 
                  name="총 발전량" 
                  stroke={COLORS.charts.total} 
                  fillOpacity={1} 
                  fill="url(#colorTotal)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4">
            <h3 className="text-sm font-medium text-neutral-800 dark:text-white mb-4">발전 에너지 구성</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {pieData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={index === 0 ? COLORS.charts.wind : COLORS.charts.piezo} 
                      />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value) => [`${value.toFixed(2)} Wh`, '발전량']}
                    contentStyle={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.9)', 
                      borderRadius: '8px',
                      boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
                      border: 'none'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4">
            <h3 className="text-sm font-medium text-neutral-800 dark:text-white mb-4">발전량 vs 소비량</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={compareData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                  <XAxis 
                    dataKey="name" 
                    tick={{ fontSize: 12 }} 
                    tickLine={false}
                    axisLine={{ stroke: '#E0E0E0' }}
                  />
                  <YAxis 
                    tick={{ fontSize: 12 }} 
                    tickLine={false}
                    axisLine={{ stroke: '#E0E0E0' }}
                  />
                  <Tooltip
                    contentStyle={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.9)', 
                      borderRadius: '8px',
                      boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
                      border: 'none'
                    }}
                    formatter={(value) => [`${value.toFixed(2)} Wh`, '전력량']}
                  />
                  <Bar dataKey="value" name="전력량">
                    {compareData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={index === 0 ? COLORS.charts.total : COLORS.charts.consumption} 
                        radius={[4, 4, 0, 0]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className={`mt-4 text-center p-2 ${isSufficient ? 'bg-green-50 dark:bg-green-900' : 'bg-red-50 dark:bg-red-900'} rounded-lg`}>
              <p className={`text-sm font-medium ${isSufficient ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'}`}>
                {isSufficient ? '잉여 발전량' : '부족한 발전량'}: {Math.abs(powerSurplus).toFixed(2)} Wh {isSufficient ? '여유' : '부족'}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Battery Dashboard
  const BatteryDashboard = () => {
    // 배터리 상태
    const batteryLevel = batteryStatus?.soc || 0;
    const batteryVoltage = batteryStatus?.voltage || 0;
    const batteryState = batteryStatus?.state || '-';
    const batteryTemp = batteryStatus?.temperature || 0;
    
    // 시간에 따른 SOC 변화 (시뮬레이션 결과 사용)
    const socData = simulationResult?.hourly_results?.map(hour => ({
      time: formatHour(hour.hour),
      level: hour.end_soc
    })) || [
      { time: '00:00', level: 50 },
      { time: '04:00', level: 30 },
      { time: '08:00', level: 45 },
      { time: '12:00', level: 70 },
      { time: '16:00', level: 65 },
      { time: '20:00', level: batteryLevel }
    ];

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatusCard
            title="배터리 충전 상태"
            value={batteryLevel}
            unit="%"
            icon="M13 10V3L4 14h7v7l9-11h-7z"
            color="indigo"
          />
          <StatusCard
            title="전압"
            value={batteryVoltage}
            unit="V"
            icon="M4 4v7l5 5 5-5v-7a1 1 0 00-1-1H5a1 1 0 00-1 1zm9 12v4h6v-8h-3v4h-3zm-9 0v4h6v-8H7v4H4z"
            color="violet"
          />
          <StatusCard
            title="상태"
            value={batteryState}
            icon="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
            color="emerald"
          />
          <StatusCard
            title="온도"
            value={batteryTemp}
            unit="K"
            icon="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
            color="yellow"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4">
            <h3 className="text-sm font-medium text-neutral-800 dark:text-white mb-4">배터리 상태</h3>
            <div className="flex flex-col md:flex-row items-center space-y-6 md:space-y-0 md:space-x-8">
              <div className="relative w-48 h-48">
                <svg className="w-48 h-48" viewBox="0 0 36 36">
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#E5E7EB"
                    strokeWidth="3"
                    className="dark:stroke-neutral-700"
                  />
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke={COLORS.secondary}
                    strokeWidth="3"
                    strokeDasharray={`${batteryLevel}, 100`}
                    className="dark:stroke-teal-500"
                  />
                  <text x="18" y="18" textAnchor="middle" className="text-4xl font-bold fill-neutral-800 dark:fill-white">
                    {batteryLevel}
                  </text>
                  <text x="18" y="24" textAnchor="middle" className="text-xl font-medium fill-neutral-500 dark:fill-neutral-400">
                    %
                  </text>
                </svg>
              </div>
              <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-neutral-50 dark:bg-neutral-900 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-neutral-500 dark:text-neutral-400">충전 상태</span>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                      batteryState.includes('CHARGING') 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : batteryState === 'DISCHARGING'
                          ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                          : 'bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200'
                    }`}>
                      {batteryState}
                    </span>
                  </div>
                  <p className="text-sm text-neutral-700 dark:text-neutral-300">
                    {batteryState.includes('CHARGING')
                      ? '현재 배터리가 충전 중입니다.'
                      : batteryState === 'DISCHARGING'
                        ? '현재 배터리가 방전 중입니다.'
                        : '현재 배터리가 대기 중입니다.'}
                  </p>
                </div>
                <div className="bg-neutral-50 dark:bg-neutral-900 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-neutral-500 dark:text-neutral-400">온도 상태</span>
                    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                      정상
                    </span>
                  </div>
                  <p className="text-sm text-neutral-700 dark:text-neutral-300">
                    현재 배터리 온도는 {batteryTemp}K로 적정 온도 범위 내에 있습니다.
                  </p>
                </div>
                <div className="bg-neutral-50 dark:bg-neutral-900 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-neutral-500 dark:text-neutral-400">전압</span>
                    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-violet-100 text-violet-800 dark:bg-violet-900 dark:text-violet-200">
                      {batteryVoltage}V
                    </span>
                  </div>
                  <p className="text-sm text-neutral-700 dark:text-neutral-300">
                    배터리 전압은 정상 범위 내에서 안정적으로 유지되고 있습니다.
                  </p>
                </div>
                <div className="bg-neutral-50 dark:bg-neutral-900 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-neutral-500 dark:text-neutral-400">배터리 상태</span>
                    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200">
                      양호
                    </span>
                  </div>
                  <p className="text-sm text-neutral-700 dark:text-neutral-300">
                    현재 배터리 건강 상태는 양호하며, 용량은 {batteryStatus?.capacity || 0}Ah입니다.
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-6 flex gap-2">
              <button 
                onClick={startBatteryCharging}
                className="flex-1 text-sm font-medium px-4 py-2 rounded-lg bg-green-100 text-green-700 hover:bg-green-200 transition-colors dark:bg-green-900 dark:text-green-300 dark:hover:bg-green-800"
              >
                충전 시작
              </button>
              <button 
                onClick={startBatteryDischarging}
                className="flex-1 text-sm font-medium px-4 py-2 rounded-lg bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800"
              >
                방전 시작
              </button>
              <button className="flex-1 text-sm font-medium px-4 py-2 rounded-lg bg-neutral-100 text-neutral-700 hover:bg-neutral-200 transition-colors dark:bg-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-700">
                대기 모드
              </button>
            </div>
          </div>

          <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4">
            <h3 className="text-sm font-medium text-neutral-800 dark:text-white mb-4">충방전 사이클</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={socData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="time" 
                    tick={{ fontSize: 12 }} 
                    tickLine={false}
                    axisLine={{ stroke: '#E0E0E0' }}
                  />
                  <YAxis 
                    tick={{ fontSize: 12 }} 
                    tickLine={false}
                    axisLine={{ stroke: '#E0E0E0' }}
                    domain={[0, 100]}
                    label={{ value: '배터리 (%)' , angle: -90, position: 'insideLeft', style: { textAnchor: 'middle' } }}
                  />
                  <Tooltip
                    contentStyle={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.9)', 
                      borderRadius: '8px',
                      boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
                      border: 'none'
                    }}
                    formatter={(value) => [`${value}%`, '배터리 레벨']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="level" 
                    name="배터리 레벨" 
                    stroke={COLORS.secondary} 
                    strokeWidth={3}
                    dot={{ fill: COLORS.secondary, strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6, fill: COLORS.secondary }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-8 mt-4">
              <div className="text-center">
                <p className="text-xs text-neutral-500 dark:text-neutral-400">총 충전량</p>
                <p className="text-lg font-semibold text-neutral-900 dark:text-white">
                  {simulationResult?.total_charge_power?.toFixed(2) || "0.00"} Wh
                </p>
              </div>
              <div className="text-center">
                <p className="text-xs text-neutral-500 dark:text-neutral-400">총 방전량</p>
                <p className="text-lg font-semibold text-neutral-900 dark:text-white">
                  {simulationResult?.total_discharge_power?.toFixed(2) || "0.00"} Wh
                </p>
              </div>
              <div className="text-center">
                <p className="text-xs text-neutral-500 dark:text-neutral-400">충방전 사이클</p>
                <p className="text-lg font-semibold text-neutral-900 dark:text-white">
                  {Math.floor(Math.random() * 100) + 150}회
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4">
          <h3 className="text-sm font-medium text-neutral-800 dark:text-white mb-4">배터리 충전 일정</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-neutral-200 dark:divide-neutral-700">
              <thead>
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">시간</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">모드</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">전력</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">예상 SOC</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">상태</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200 dark:divide-neutral-700">
                {(dailySchedule?.hourly_plan || [])
                  .filter(plan => plan.ess_mode !== 'IDLE')
                  .slice(0, 5)
                  .map((plan, index) => {
                    const now = new Date();
                    const hour = now.getHours();
                    let status = '';
                    if (plan.hour < hour) status = '완료';
                    else if (plan.hour === hour) status = '진행중';
                    else status = '예정';
                    
                    return (
                      <tr key={index} className={index % 2 === 0 ? 'bg-neutral-50 dark:bg-neutral-900' : ''}>
                        <td className="px-3 py-3 text-sm text-neutral-900 dark:text-white">
                          {`${plan.hour}:00 - ${plan.hour + 1}:00`}
                        </td>
                        <td className="px-3 py-3 text-sm">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            plan.ess_mode === 'CHARGING' 
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                              : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                          }`}>
                            {plan.ess_mode === 'CHARGING' ? '충전' : '방전'}
                          </span>
                        </td>
                        <td className="px-3 py-3 text-sm text-neutral-900 dark:text-white">
                          {Math.abs(plan.ess_power).toFixed(2)} Wh
                        </td>
                        <td className="px-3 py-3 text-sm text-neutral-900 dark:text-white">
                          {index === 0 
                            ? `${batteryLevel}% → ${batteryLevel + 15}%` 
                            : `${batteryLevel + 15 * index}% → ${batteryLevel + 15 * (index + 1)}%`}
                        </td>
                        <td className="px-3 py-3 text-sm">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            status === '완료' 
                              ? 'bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200' 
                              : status === '진행중'
                                ? 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200'
                                : 'bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200'
                          }`}>
                            {status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  // 적절한 대시보드 렌더링
  const renderDashboard = () => {
    switch (view) {
      case 'overview':
        return <OverviewDashboard />;
      case 'power':
        return <PowerDashboard />;
      case 'battery':
        return <BatteryDashboard />;
      case 'analytics':
        return <AnalyticsDashboard />;
      case 'settings':
        return <SettingsDashboard />;
      default:
        return <OverviewDashboard />;
    }
  };

  return (
    <div className={`min-h-screen bg-neutral-100 dark:bg-neutral-900 ${theme === 'dark' ? 'dark' : ''}`}>
      {/* 로딩 오버레이 */}
      <LoadingOverlay />
      
      {/* 사이드바 */}
      <SidebarNavigation />
      
      {/* 메인 콘텐츠 */}
      <div className={`transition-all duration-300 ${showSidebar ? 'pl-64' : 'pl-16'}`}>
        <div className="p-6">
          <DashboardHeader />
          
          {/* 오류 표시 */}
          <ErrorDisplay />
          
          {/* 대시보드 콘텐츠 */}
          <main className="mt-6">
            {renderDashboard()}
          </main>
          
          {/* 푸터 */}
          <footer className="mt-8 text-center text-sm text-neutral-500 dark:text-neutral-400">
            <p>전력 발전량 통합 시스템 v2.0.0 &copy; {new Date().getFullYear()} - 인하대학교</p>
          </footer>
        </div>
      </div>
    </div>
  );
};

export default EnhancedDashboard;
  
  // Analytics Dashboard
  const AnalyticsDashboard = () => {
    // 각 기간별 데이터의 합계 및 평균 계산
    const totalAnnualProduction = annualPower?.annual_total_power_kwh || 0;
    const avgDailyProduction = totalAnnualProduction / 365 || 0;
    const overallSufficiency = annualPower?.sufficiency_percentage || 0;
    const costSavings = totalAnnualProduction * 120; // 120원/kWh 가정
    
    // Settings Dashboard
  const SettingsDashboard = () => {
    return (
      <div className="space-y-6">
        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-medium text-neutral-800 dark:text-white mb-6">대시보드 설정</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-neutral-800 dark:text-white mb-4">일반 설정</h4>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-neutral-600 dark:text-neutral-400 mb-1">대시보드 이름</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary dark:bg-neutral-900 dark:text-white"
                    value="인하대학교 전력 발전량 대시보드"
                  />
                </div>
                <div>
                  <label className="block text-sm text-neutral-600 dark:text-neutral-400 mb-1">자동 새로고침</label>
                  <select className="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary appearance-none dark:bg-neutral-900 dark:text-white">
                    <option>30초</option>
                    <option>1분</option>
                    <option>5분</option>
                    <option>10분</option>
                    <option>사용 안함</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-neutral-600 dark:text-neutral-400 mb-1">테마</label>
                  <div className="flex items-center space-x-4">
                    <label className="flex items-center">
                      <input type="radio" name="theme" className="mr-2" checked={theme === 'light'} onChange={() => setTheme('light')} />
                      <span className="text-sm text-neutral-600 dark:text-neutral-400">라이트</span>
                    </label>
                    <label className="flex items-center">
                      <input type="radio" name="theme" className="mr-2" checked={theme === 'dark'} onChange={() => setTheme('dark')} />
                      <span className="text-sm text-neutral-600 dark:text-neutral-400">다크</span>
                    </label>
                    <label className="flex items-center">
                      <input type="radio" name="theme" className="mr-2" />
                      <span className="text-sm text-neutral-600 dark:text-neutral-400">자동</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium text-neutral-800 dark:text-white mb-4">시스템 설정</h4>
              <div className="space-y-4">
                <div>
                  <label className="flex items-center justify-between text-sm text-neutral-600 dark:text-neutral-400 mb-1">
                    <span>알림 활성화</span>
                    <span className="relative inline-block w-10 h-5 rounded-full bg-neutral-200 dark:bg-neutral-700 transition-colors cursor-pointer">
                      <span className="absolute left-1 top-1 w-3 h-3 rounded-full bg-white transition-transform"></span>
                    </span>
                  </label>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400">
                    전력 발전량 및 배터리 상태 변화에 대한 알림을 받습니다.
                  </p>
                </div>
                <div>
                  <label className="flex items-center justify-between text-sm text-neutral-600 dark:text-neutral-400 mb-1">
                    <span>자동 충방전 스케줄링</span>
                    <span className="relative inline-block w-10 h-5 rounded-full bg-green-500 transition-colors cursor-pointer">
                      <span className="absolute left-5 top-1 w-3 h-3 rounded-full bg-white transition-transform"></span>
                    </span>
                  </label>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400">
                    배터리의 충전 및 방전 일정을 자동으로 최적화합니다.
                  </p>
                </div>
                <div>
                  <label className="flex items-center justify-between text-sm text-neutral-600 dark:text-neutral-400 mb-1">
                    <span>데이터 백업</span>
                    <span className="relative inline-block w-10 h-5 rounded-full bg-neutral-200 dark:bg-neutral-700 transition-colors cursor-pointer">
                      <span className="absolute left-1 top-1 w-3 h-3 rounded-full bg-white transition-transform"></span>
                    </span>
                  </label>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400">
                    발전량 및 배터리 데이터를 클라우드에 자동으로 백업합니다.
                  </p>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-6 pt-6 border-t border-neutral-200 dark:border-neutral-700 flex justify-end">
            <button className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-opacity-90 transition-colors">
              설정 저장
            </button>
          </div>
        </div>

        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-medium text-neutral-800 dark:text-white mb-6">배터리 설정</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-neutral-800 dark:text-white mb-4">충전 설정</h4>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-neutral-600 dark:text-neutral-400 mb-1">최대 충전 C-rate</label>
                  <div className="flex items-center">
                    <input
                      type="range"
                      min="0.1"
                      max="2.0"
                      step="0.1"
                      value="0.5"
                      className="w-full h-1 bg-neutral-300 dark:bg-neutral-700 rounded-lg appearance-none"
                    />
                    <span className="ml-2 text-sm font-medium text-neutral-900 dark:text-white">0.5C</span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-neutral-600 dark:text-neutral-400 mb-1">충전 중단 SOC</label>
                  <div className="flex items-center">
                    <input
                      type="range"
                      min="80"
                      max="100"
                      step="1"
                      value="90"
                      className="w-full h-1 bg-neutral-300 dark:bg-neutral-700 rounded-lg appearance-none"
                    />
                    <span className="ml-2 text-sm font-medium text-neutral-900 dark:text-white">90%</span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-neutral-600 dark:text-neutral-400 mb-1">충전 우선 시간대</label>
                  <select className="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary appearance-none dark:bg-neutral-900 dark:text-white">
                    <option>09:00 - 15:00</option>
                    <option>10:00 - 16:00</option>
                    <option>12:00 - 18:00</option>
                    <option>항상 사용</option>
                  </select>
                </div>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium text-neutral-800 dark:text-white mb-4">방전 설정</h4>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-neutral-600 dark:text-neutral-400 mb-1">최대 방전 C-rate</label>
                  <div className="flex items-center">
                    <input
                      type="range"
                      min="0.1"
                      max="2.0"
                      step="0.1"
                      value="0.3"
                      className="w-full h-1 bg-neutral-300 dark:bg-neutral-700 rounded-lg appearance-none"
                    />
                    <span className="ml-2 text-sm font-medium text-neutral-900 dark:text-white">0.3C</span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-neutral-600 dark:text-neutral-400 mb-1">방전 중단 SOC</label>
                  <div className="flex items-center">
                    <input
                      type="range"
                      min="10"
                      max="40"
                      step="1"
                      value="20"
                      className="w-full h-1 bg-neutral-300 dark:bg-neutral-700 rounded-lg appearance-none"
                    />
                    <span className="ml-2 text-sm font-medium text-neutral-900 dark:text-white">20%</span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-neutral-600 dark:text-neutral-400 mb-1">방전 우선 시간대</label>
                  <select className="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary appearance-none dark:bg-neutral-900 dark:text-white">
                    <option>18:00 - 24:00</option>
                    <option>19:00 - 01:00</option>
                    <option>20:00 - 02:00</option>
                    <option>항상 사용</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-6 pt-6 border-t border-neutral-200 dark:border-neutral-700 flex justify-end">
            <button className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-opacity-90 transition-colors">
              설정 저장
            </button>
          </div>
        </div>
      </div>
    );
  };

  // 월별 비교 데이터 생성
    const monthlyComparisonData = [
      { month: '1월', current: (annualPower?.monthly_results[0]?.monthly_total_power_wh || 0) / 1000, previous: ((annualPower?.monthly_results[0]?.monthly_total_power_wh || 0) / 1000) * 0.85 },
      { month: '2월', current: (annualPower?.monthly_results[1]?.monthly_total_power_wh || 0) / 1000, previous: ((annualPower?.monthly_results[1]?.monthly_total_power_wh || 0) / 1000) * 0.88 },
      { month: '3월', current: (annualPower?.monthly_results[2]?.monthly_total_power_wh || 0) / 1000, previous: ((annualPower?.monthly_results[2]?.monthly_total_power_wh || 0) / 1000) * 0.87 },
      { month: '4월', current: (annualPower?.monthly_results[3]?.monthly_total_power_wh || 0) / 1000, previous: ((annualPower?.monthly_results[3]?.monthly_total_power_wh || 0) / 1000) * 0.9 },
      { month: '5월', current: (annualPower?.monthly_results[4]?.monthly_total_power_wh || 0) / 1000, previous: ((annualPower?.monthly_results[4]?.monthly_total_power_wh || 0) / 1000) * 0.85 },
      { month: '6월', current: (annualPower?.monthly_results[5]?.monthly_total_power_wh || 0) / 1000, previous: ((annualPower?.monthly_results[5]?.monthly_total_power_wh || 0) / 1000) * 0.92 }
    ];
    
    // 충족률 변화 추이 데이터
    const sufficiencyTrendData = annualPower?.monthly_results?.map(month => ({
      month: month.month,
      value: month.sufficiency_percentage
    })) || [];
    
    // 연간 요약 데이터
    const annualRecords = [
      { 
        period: '2025', 
        wind: formatEnergy(annualPower?.annual_wind_power_wh || 0, 'kWh'), 
        piezo: formatEnergy(annualPower?.annual_piezo_power_wh || 0, 'kWh'), 
        total: formatEnergy(annualPower?.annual_total_power_wh || 0, 'kWh'), 
        sufficiency: `${annualPower?.sufficiency_percentage?.toFixed(1) || 0}%`, 
        windSpeed: `${annualPower?.avg_wind_speed || 3.5} m/s` 
      },
      { 
        period: '2024', 
        wind: formatEnergy((annualPower?.annual_wind_power_wh || 0) * 0.92, 'kWh'), 
        piezo: formatEnergy((annualPower?.annual_piezo_power_wh || 0) * 0.94, 'kWh'), 
        total: formatEnergy((annualPower?.annual_total_power_wh || 0) * 0.92, 'kWh'), 
        sufficiency: `${((annualPower?.sufficiency_percentage || 0) * 0.92).toFixed(1)}%`, 
        windSpeed: '3.3 m/s' 
      },
      { 
        period: '2023', 
        wind: formatEnergy((annualPower?.annual_wind_power_wh || 0) * 0.85, 'kWh'), 
        piezo: formatEnergy((annualPower?.annual_piezo_power_wh || 0) * 0.88, 'kWh'), 
        total: formatEnergy((annualPower?.annual_total_power_wh || 0) * 0.85, 'kWh'), 
        sufficiency: `${((annualPower?.sufficiency_percentage || 0) * 0.85).toFixed(1)}%`, 
        windSpeed: '3.1 m/s' 
      }
    ];

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatusCard
            title="총 발전량 (연간)"
            value={totalAnnualProduction.toFixed(1)}
            unit="kWh"
            icon="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
            color="blue"
            change="8.2"
            isIncreasing={true}
          />
          <StatusCard
            title="평균 발전량 (일간)"
            value={avgDailyProduction.toFixed(1)}
            unit="kWh"
            icon="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            color="green"
            change="5.3"
            isIncreasing={true}
          />
          <StatusCard
            title="평균 충족률"
            value={overallSufficiency.toFixed(1)}
            unit="%"
            icon="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"
            color="amber"
            change="7.5"
            isIncreasing={true}
          />
          <StatusCard
            title="비용 절감액 (연간)"
            value={costSavings.toLocaleString()}
            unit="원"
            icon="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            color="emerald"
            change="10.2"
            isIncreasing={true}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4">
            <h3 className="text-sm font-medium text-neutral-800 dark:text-white mb-4">월간 발전량 비교</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyComparisonData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                  <XAxis 
                    dataKey="month" 
                    tick={{ fontSize: 12 }} 
                    tickLine={false}
                    axisLine={{ stroke: '#E0E0E0' }}
                  />
                  <YAxis 
                    tick={{ fontSize: 12 }} 
                    tickLine={false}
                    axisLine={{ stroke: '#E0E0E0' }}
                  />
                  <Tooltip
                    contentStyle={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.9)', 
                      borderRadius: '8px',
                      boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
                      border: 'none'
                    }}
                    formatter={(value) => [`${value.toFixed(2)} kWh`, '발전량']}
                  />
                  <Legend iconType="circle" />
                  <Bar dataKey="current" name="2025년" fill={COLORS.charts.wind} radius={[4, 4, 0, 0]} />
                  <Bar dataKey="previous" name="2024년" fill="#ccc" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4">
            <h3 className="text-sm font-medium text-neutral-800 dark:text-white mb-4">충족률 변화 추이</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={sufficiencyTrendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="month" 
                    tick={{ fontSize: 12 }} 
                    tickLine={false}
                    axisLine={{ stroke: '#E0E0E0' }}
                  />
                  <YAxis 
                    tick={{ fontSize: 12 }} 
                    tickLine={false}
                    axisLine={{ stroke: '#E0E0E0' }}
                  />
                  <Tooltip
                    contentStyle={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.9)', 
                      borderRadius: '8px',
                      boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
                      border: 'none'
                    }}
                    formatter={(value) => [`${value.toFixed(1)}%`, '충족률']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    name="충족률" 
                    stroke={COLORS.charts.total} 
                    strokeWidth={3}
                    dot={{ fill: COLORS.charts.total, strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6, fill: COLORS.charts.total }}
                  />
                  <ReferenceLine y={100} stroke="red" strokeDasharray="3 3" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-medium text-neutral-800 dark:text-white">발전 기록 요약</h3>
            <div className="flex items-center space-x-2">
              <button className="text-xs px-2 py-1 rounded bg-primary bg-opacity-10 text-primary">연간</button>
              <button className="text-xs px-2 py-1 rounded text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-700">월간</button>
              <button className="text-xs px-2 py-1 rounded text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-700">주간</button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-neutral-200 dark:divide-neutral-700">
              <thead>
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">기간</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">풍력 발전량</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">지압 발전량</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">총 발전량</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">충족률</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">평균 풍속</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200 dark:divide-neutral-700">
                {annualRecords.map((record, index) => (
                  <tr key={index} className={index % 2 === 0 ? 'bg-neutral-50 dark:bg-neutral-900' : ''}>
                    <td className="px-3 py-3 text-sm font-medium text-neutral-900 dark:text-white">{record.period}</td>
                    <td className="px-3 py-3 text-sm text-neutral-900 dark:text-white">{record.wind}</td>
                    <td className="px-3 py-3 text-sm text-neutral-900 dark:text-white">{record.piezo}</td>
                    <td className="px-3 py-3 text-sm text-neutral-900 dark:text-white">{record.total}</td>
                    <td className="px-3 py-3 text-sm">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        parseFloat(record.sufficiency) >= 100 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                          : 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200'
                      }`}>
                        {record.sufficiency}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-sm text-neutral-900 dark:text-white">{record.windSpeed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };