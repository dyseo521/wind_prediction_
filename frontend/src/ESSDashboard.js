import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  RadialBarChart, RadialBar, ResponsiveContainer, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, Label, ReferenceLine 
} from 'recharts';

// API 기본 URL 설정 (환경변수 사용)
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

// 색상 설정
const COLORS = {
  charging: '#82ca9d',
  discharging: '#8884d8',
  idle: '#d3d3d3',
  rest: '#ffc658',
  soc: '#0088FE',
  lowSoc: '#FF8042',
  criticalSoc: '#FF0000',
  blue: ['#8884d8', '#7366bd', '#5e48a2', '#493a87', '#342c6c'],
  green: ['#82ca9d', '#6eb589', '#5a9f75', '#468a61', '#32754c'],
  orange: ['#ff8042', '#e67037', '#cc5f2d', '#b35022', '#994118']
};

const ESSDashboard = () => {
  // 상태 관리
  const [activeTab, setActiveTab] = useState('status');
  const [selectedLocation, setSelectedLocation] = useState('5호관_60주년_사이');
  const [batteryStatus, setBatteryStatus] = useState(null);
  const [realtimeStatus, setRealtimeStatus] = useState(null);
  const [dailySchedule, setDailySchedule] = useState(null);
  const [simulationResult, setSimulationResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [windSpeed, setWindSpeed] = useState(3.5);

  // 위치 옵션
  const locationOptions = [
    { value: '5호관_60주년_사이', label: '5호관-60주년 사이' },
    { value: '인경호_앞', label: '인경호 앞' },
    { value: '하이데거숲', label: '하이데거숲' }
  ];

  // API 호출 함수
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

  // 배터리 상태 조회
  const fetchBatteryStatus = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await fetchData(`${API_BASE_URL}/ess/battery/status`);
      setBatteryStatus(data);
    } catch (err) {
      console.error('배터리 상태 조회 오류:', err);
      setError(err.message || '배터리 상태 조회 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 실시간 ESS 상태 조회
  const fetchRealtimeStatus = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await fetchData(`${API_BASE_URL}/ess/realtime/${selectedLocation}`);
      setRealtimeStatus(data);
    } catch (err) {
      console.error('실시간 ESS 상태 조회 오류:', err);
      setError(err.message || '실시간 ESS 상태 조회 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 일간 ESS 스케줄 조회
  const fetchDailySchedule = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await fetchData(`${API_BASE_URL}/ess/daily-schedule/${selectedLocation}?avg_wind_speed=${windSpeed}`);
      setDailySchedule(data);
    } catch (err) {
      console.error('일간 ESS 스케줄 조회 오류:', err);
      setError(err.message || '일간 ESS 스케줄 조회 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // ESS 시뮬레이션 실행
  const runEssSimulation = async () => {
    setLoading(true);
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
      setLoading(false);
    }
  };

  // 배터리 충전 요청
  const startBatteryCharging = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 현재 전력 생산량 가져오기 (실시간 상태에서)
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
      setLoading(false);
    }
  };

  // 배터리 방전 요청
  const startBatteryDischarging = async () => {
    setLoading(true);
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
      setLoading(false);
    }
  };

  // 데이터 새로고침
  const refreshData = () => {
    if (activeTab === 'status') {
      fetchBatteryStatus();
    } else if (activeTab === 'realtime') {
      fetchRealtimeStatus();
    } else if (activeTab === 'schedule') {
      fetchDailySchedule();
    } else if (activeTab === 'simulation') {
      runEssSimulation();
    }
  };

  // 위치나 탭 변경 시 데이터 새로고침
  useEffect(() => {
    refreshData();
    
    // 실시간 상태 탭에서는 10초마다 자동 새로고침
    let intervalId = null;
    if (activeTab === 'realtime') {
      intervalId = setInterval(() => {
        fetchRealtimeStatus();
      }, 10000);
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [selectedLocation, activeTab]);

  // 배터리 상태 색상 결정
  const getBatteryStateColor = (state) => {
    if (state === 'CHARGING_CC' || state === 'CHARGING_CV') return COLORS.charging;
    if (state === 'DISCHARGING') return COLORS.discharging;
    if (state === 'REST') return COLORS.rest;
    return COLORS.idle;
  };

  // SOC 색상 결정
  const getSocColor = (soc) => {
    if (soc >= 70) return COLORS.soc;
    if (soc >= 30) return COLORS.lowSoc;
    return COLORS.criticalSoc;
  };

  // 시간 포맷 변환
  const formatHour = (hour) => {
    return `${hour}:00`;
  };

  // 탭 메뉴 렌더링
  const renderTabs = () => (
    <div className="mb-6 border-b border-gray-200">
      <ul className="flex flex-wrap -mb-px text-sm font-medium text-center">
        <li className="mr-2">
          <button
            className={`inline-block p-4 rounded-t-lg ${activeTab === 'status' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-600'}`}
            onClick={() => setActiveTab('status')}
          >
            배터리 상태
          </button>
        </li>
        <li className="mr-2">
          <button
            className={`inline-block p-4 rounded-t-lg ${activeTab === 'realtime' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-600'}`}
            onClick={() => setActiveTab('realtime')}
          >
            실시간 ESS
          </button>
        </li>
        <li className="mr-2">
          <button
            className={`inline-block p-4 rounded-t-lg ${activeTab === 'schedule' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-600'}`}
            onClick={() => setActiveTab('schedule')}
          >
            일간 스케줄
          </button>
        </li>
        <li className="mr-2">
          <button
            className={`inline-block p-4 rounded-t-lg ${activeTab === 'simulation' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-600'}`}
            onClick={() => setActiveTab('simulation')}
          >
            ESS 시뮬레이션
          </button>
        </li>
      </ul>
    </div>
  );

  // 위치 선택 및 설정 렌더링
  const renderControls = () => (
    <div className="mb-6 flex flex-wrap gap-4 items-center">
      <div className="min-w-64">
        <label className="block text-sm font-medium text-gray-700 mb-1">위치 선택</label>
        <select
          value={selectedLocation}
          onChange={(e) => setSelectedLocation(e.target.value)}
          className="w-full p-2 border rounded"
        >
          {locationOptions.map(option => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      </div>

      {(activeTab === 'schedule' || activeTab === 'simulation') && (
        <div className="min-w-64">
          <label className="block text-sm font-medium text-gray-700 mb-1">평균 풍속 (m/s)</label>
          <div className="flex items-center gap-2">
            <input
              type="range"
              min="0.5"
              max="10"
              step="0.1"
              value={windSpeed}
              onChange={(e) => setWindSpeed(parseFloat(e.target.value))}
              className="w-40"
            />
            <span className="text-sm font-semibold">{windSpeed} m/s</span>
          </div>
        </div>
      )}

      {activeTab === 'status' && (
        <div className="flex gap-2">
          <button
            onClick={startBatteryCharging}
            disabled={loading}
            className={`px-4 py-2 rounded ${loading ? 'bg-gray-400' : 'bg-green-600 text-white hover:bg-green-700'}`}
          >
            충전 시작
          </button>
          <button
            onClick={startBatteryDischarging}
            disabled={loading}
            className={`px-4 py-2 rounded ${loading ? 'bg-gray-400' : 'bg-blue-600 text-white hover:bg-blue-700'}`}
          >
            방전 시작
          </button>
        </div>
      )}

      <div className="ml-auto">
        <button
          onClick={refreshData}
          disabled={loading}
          className={`px-4 py-2 rounded ${loading ? 'bg-gray-400' : 'bg-blue-600 text-white hover:bg-blue-700'}`}
        >
          {loading ? '로딩 중...' : '새로고침'}
        </button>
      </div>
    </div>
  );

  // 배터리 상태 대시보드 렌더링
  const renderBatteryStatusDashboard = () => {
    if (!batteryStatus) {
      return (
        <div className="text-center py-8 text-gray-500">
          <p>배터리 상태 데이터를 불러오는 중입니다. '새로고침' 버튼을 눌러주세요.</p>
        </div>
      );
    }

    // SOC 게이지 데이터
    const socData = [
      { name: 'SOC', value: batteryStatus.soc }
    ];

    return (
      <div className="space-y-6">
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-xl font-semibold mb-4">배터리 상태 요약</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className={`p-4 rounded bg-${getBatteryStateColor(batteryStatus.state)}-50`}>
              <h3 className="text-sm font-medium text-gray-600">시스템 상태</h3>
              <p className="text-2xl font-bold text-gray-800">{batteryStatus.state}</p>
            </div>
            
            <div className="bg-blue-50 p-4 rounded">
              <h3 className="text-sm font-medium text-gray-600">SOC (충전 상태)</h3>
              <p className="text-2xl font-bold text-blue-700">{batteryStatus.soc}%</p>
            </div>
            
            <div className="bg-green-50 p-4 rounded">
              <h3 className="text-sm font-medium text-gray-600">셀 전압</h3>
              <p className="text-2xl font-bold text-green-700">{batteryStatus.voltage}V</p>
            </div>
            
            <div className="bg-purple-50 p-4 rounded">
              <h3 className="text-sm font-medium text-gray-600">팩 전압</h3>
              <p className="text-2xl font-bold text-purple-700">{batteryStatus.pack_voltage}V</p>
            </div>
          </div>
          
          <div className="mt-4 p-4 bg-gray-50 rounded">
            <h3 className="text-sm font-medium text-gray-600 mb-2">배터리 구성</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-gray-500">셀 구성</p>
                <p className="font-semibold">{batteryStatus.cell_configuration}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">총 셀 수</p>
                <p className="font-semibold">{batteryStatus.total_cells}개</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">용량</p>
                <p className="font-semibold">{batteryStatus.capacity}Ah</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">온도</p>
                <p className="font-semibold">{batteryStatus.temperature}K</p>
              </div>
            </div>
          </div>

          {batteryStatus.rest_info && (
            <div className="mt-4 p-4 bg-yellow-50 rounded">
              <h3 className="text-sm font-medium text-gray-600 mb-2">휴식 상태 정보</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-xs text-gray-500">시작 시간</p>
                  <p className="font-semibold">{new Date(batteryStatus.rest_info.start_time).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">경과 시간</p>
                  <p className="font-semibold">{batteryStatus.rest_info.elapsed_minutes}분</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">남은 시간</p>
                  <p className="font-semibold">{batteryStatus.rest_info.remaining_minutes}분</p>
                </div>
              </div>
            </div>
          )}
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded shadow">
            <h3 className="text-lg font-semibold mb-4">SOC (충전 상태)</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart 
                  cx="50%" 
                  cy="50%" 
                  innerRadius="30%" 
                  outerRadius="80%" 
                  barSize={30} 
                  data={socData} 
                  startAngle={90} 
                  endAngle={-270}
                >
                  <RadialBar
                    minAngle={15}
                    background
                    clockWise
                    dataKey="value"
                    cornerRadius={10}
                    fill={getSocColor(batteryStatus.soc)}
                  />
                  <Label
                    value={`${batteryStatus.soc}%`}
                    position="center"
                    fill="#333"
                    style={{ fontSize: '30px', fontWeight: 'bold' }}
                  />
                </RadialBarChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded shadow">
            <h3 className="text-lg font-semibold mb-4">시스템 상태</h3>
            <div className="flex flex-col items-center justify-center h-64">
              <div className={`w-32 h-32 rounded-full flex items-center justify-center text-white text-lg font-bold bg-${getBatteryStateColor(batteryStatus.state)}`}>
                {batteryStatus.state}
              </div>
              <div className="mt-4 text-center">
                {batteryStatus.state === 'CHARGING_CC' && <p>정전류(CC) 충전 중: {batteryStatus.charge_current?.toFixed(2)}A</p>}
                {batteryStatus.state === 'CHARGING_CV' && <p>정전압(CV) 충전 중: {batteryStatus.voltage}V</p>}
                {batteryStatus.state === 'DISCHARGING' && <p>방전 중: {batteryStatus.discharge_current?.toFixed(2)}A</p>}
                {batteryStatus.state === 'REST' && <p>휴식 중: 남은 시간 {batteryStatus.rest_info?.remaining_minutes}분</p>}
                {batteryStatus.state === 'IDLE' && <p>대기 중: 충전 또는 방전 명령 대기</p>}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // 실시간 ESS 대시보드 렌더링
  const renderRealtimeEssDashboard = () => {
    if (!realtimeStatus) {
      return (
        <div className="text-center py-8 text-gray-500">
          <p>실시간 ESS 데이터를 불러오는 중입니다. '새로고침' 버튼을 눌러주세요.</p>
        </div>
      );
    }

    // 배터리 상태
    const batteryStatus = realtimeStatus.battery_status;
    
    // 날씨 정보
    const weather = realtimeStatus.weather;

    return (
      <div className="space-y-6">
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-xl font-semibold mb-4">실시간 ESS 상태</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded">
              <h3 className="text-sm font-medium text-gray-600">위치</h3>
              <p className="text-lg font-bold text-blue-700">{realtimeStatus.location}</p>
            </div>
            
            <div className={`p-4 rounded ${realtimeStatus.is_nighttime ? 'bg-indigo-50' : 'bg-yellow-50'}`}>
              <h3 className="text-sm font-medium text-gray-600">시간대</h3>
              <p className="text-lg font-bold">{realtimeStatus.is_nighttime ? '야간 (방전)' : '주간 (충전)'}</p>
            </div>
            
            <div className="bg-green-50 p-4 rounded">
              <h3 className="text-sm font-medium text-gray-600">전력 생산량</h3>
              <p className="text-lg font-bold text-green-700">{realtimeStatus.power_production?.toFixed(2)} Wh</p>
            </div>
            
            <div className={`p-4 rounded bg-${getBatteryStateColor(realtimeStatus.ess_state)}-50`}>
              <h3 className="text-sm font-medium text-gray-600">ESS 상태</h3>
              <p className="text-lg font-bold">{realtimeStatus.ess_state}</p>
            </div>
          </div>
          
          <div className="mt-4 p-4 bg-gray-50 rounded">
            <h3 className="text-sm font-medium text-gray-600 mb-2">날씨 조건</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-gray-500">풍속</p>
                <p className="font-semibold">{realtimeStatus.wind_speed} m/s</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">기온</p>
                <p className="font-semibold">{weather.temperature}°C</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">습도</p>
                <p className="font-semibold">{weather.humidity}%</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">현재 시간</p>
                <p className="font-semibold">{new Date(realtimeStatus.current_time).toLocaleTimeString()}</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded shadow">
            <h3 className="text-lg font-semibold mb-4">배터리 상태</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart 
                  cx="50%" 
                  cy="50%" 
                  innerRadius="30%" 
                  outerRadius="80%" 
                  barSize={30} 
                  data={[{ name: 'SOC', value: batteryStatus.soc }]} 
                  startAngle={90} 
                  endAngle={-270}
                >
                  <RadialBar
                    minAngle={15}
                    background
                    clockWise
                    dataKey="value"
                    cornerRadius={10}
                    fill={getSocColor(batteryStatus.soc)}
                  />
                  <Label
                    value={`${batteryStatus.soc}%`}
                    position="center"
                    fill="#333"
                    style={{ fontSize: '30px', fontWeight: 'bold' }}
                  />
                </RadialBarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-gray-500">셀 전압</p>
                <p className="font-semibold">{batteryStatus.voltage}V</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">팩 전압</p>
                <p className="font-semibold">{batteryStatus.pack_voltage}V</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded shadow">
            <h3 className="text-lg font-semibold mb-4">ESS 제어 정보</h3>
            <div className="space-y-4">
              {realtimeStatus.is_nighttime ? (
                // 야간 - 방전 정보
                <div className="p-4 bg-indigo-50 rounded">
                  <h4 className="font-semibold mb-2">야간 방전 정보</h4>
                  {realtimeStatus.streetlight_support ? (
                    <div className="space-y-2">
                      <p><span className="font-semibold">가로등 소비 전력:</span> {realtimeStatus.streetlight_support.power_required?.toFixed(2)} Wh</p>
                      <p><span className="font-semibold">배터리 공급 전력:</span> {realtimeStatus.streetlight_support.power_from_battery?.toFixed(2)} Wh</p>
                      <p><span className="font-semibold">배터리 기여도:</span> {realtimeStatus.streetlight_support.battery_contribution_percentage?.toFixed(1)}%</p>
                    </div>
                  ) : (
                    <p>방전 중이 아니거나 가로등 지원 정보가 없습니다.</p>
                  )}
                </div>
              ) : (
                // 주간 - 충전 정보
                <div className="p-4 bg-yellow-50 rounded">
                  <h4 className="font-semibold mb-2">주간 충전 정보</h4>
                  {realtimeStatus.charging_info ? (
                    <div className="space-y-2">
                      <p><span className="font-semibold">충전 C-rate:</span> {realtimeStatus.charging_info.current_c_rate?.toFixed(3)}C</p>
                      <p><span className="font-semibold">충전 전류:</span> {realtimeStatus.charging_info.charge_current?.toFixed(3)}A</p>
                      <p><span className="font-semibold">완전 충전 예상 시간:</span> 약 {realtimeStatus.charging_info.estimated_full_charge_time?.toFixed(1)}시간</p>
                    </div>
                  ) : (
                    <p>충전 중이 아니거나 충전 정보가 없습니다.</p>
                  )}
                </div>
              )}
              
              <div className="p-4 bg-gray-50 rounded">
                <h4 className="font-semibold mb-2">ESS 제어 결과</h4>
                <p><span className="font-semibold">상태:</span> {realtimeStatus.ess_control.state}</p>
                {realtimeStatus.ess_control.message && (
                  <p><span className="font-semibold">메시지:</span> {realtimeStatus.ess_control.message}</p>
                )}
                {realtimeStatus.ess_control.c_rate && (
                  <p><span className="font-semibold">C-rate:</span> {realtimeStatus.ess_control.c_rate.toFixed(3)}C</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // 일간 ESS 스케줄 대시보드 렌더링
  const renderDailyScheduleDashboard = () => {
    if (!dailySchedule) {
      return (
        <div className="text-center py-8 text-gray-500">
          <p>일간 ESS 스케줄 데이터를 불러오는 중입니다. '새로고침' 버튼을 눌러주세요.</p>
        </div>
      );
    }

    // 시간별 계획 데이터 변환
    const hourlyPlanData = dailySchedule.hourly_plan.map(plan => ({
      hour: plan.hour,
      label: formatHour(plan.hour),
      production: plan.power_production,
      consumption: plan.power_consumption,
      essPower: plan.ess_power,
      essMode: plan.ess_mode,
      isCharging: plan.ess_mode === 'CHARGING',
      isDischarging: plan.ess_mode === 'DISCHARGING'
    }));

    return (
      <div className="space-y-6">
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-xl font-semibold mb-4">일간 ESS 스케줄 요약</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded">
              <h3 className="text-sm font-medium text-gray-600">위치</h3>
              <p className="text-lg font-bold text-blue-700">{dailySchedule.location}</p>
            </div>
            
            <div className="bg-green-50 p-4 rounded">
              <h3 className="text-sm font-medium text-gray-600">총 전력 생산량</h3>
              <p className="text-lg font-bold text-green-700">{dailySchedule.total_power_production_wh.toFixed(2)} Wh</p>
            </div>
            
            <div className="bg-orange-50 p-4 rounded">
              <h3 className="text-sm font-medium text-gray-600">총 가로등 소비량</h3>
              <p className="text-lg font-bold text-orange-700">{dailySchedule.total_streetlight_consumption_wh.toFixed(2)} Wh</p>
            </div>
            
            <div className={`p-4 rounded ${dailySchedule.ess_summary.is_sufficient ? 'bg-green-50' : 'bg-red-50'}`}>
              <h3 className="text-sm font-medium text-gray-600">배터리 용량 충족도</h3>
              <p className={`text-lg font-bold ${dailySchedule.ess_summary.is_sufficient ? 'text-green-700' : 'text-red-700'}`}>
                {dailySchedule.ess_summary.is_sufficient ? '충분' : '부족'}
              </p>
            </div>
          </div>
          
          <div className="mt-4 p-4 bg-gray-50 rounded">
            <h3 className="text-sm font-medium text-gray-600 mb-2">ESS 운영 요약</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <p className="text-xs text-gray-500">필요 배터리 용량</p>
                <p className="font-semibold">{dailySchedule.ess_summary.required_battery_capacity_wh.toFixed(2)} Wh</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">충전 기간</p>
                <p className="font-semibold">{dailySchedule.ess_summary.charging_period}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">방전 기간</p>
                <p className="font-semibold">{dailySchedule.ess_summary.discharging_period}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">최대 충전 용량</p>
                <p className="font-semibold">{dailySchedule.ess_summary.max_charging_capacity_wh.toFixed(2)} Wh</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">충방전 밸런스</p>
                <p className={`font-semibold ${dailySchedule.ess_summary.charge_discharge_balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {dailySchedule.ess_summary.charge_discharge_balance.toFixed(2)} Wh
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded shadow">
  <h3 className="text-lg font-semibold mb-4">시간별 ESS 운영 계획</h3>
  <div className="h-96">
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={hourlyPlanData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="label"
          tick={{ fontSize: 12 }}
          interval={2}
          label={{ value: '시간', position: 'insideBottom', offset: -5 }}
        />
        <YAxis 
          label={{ value: '전력량 (Wh)', angle: -90, position: 'insideLeft' }}
          domain={['auto', 'auto']}
        />
        <Tooltip 
          formatter={(value, name) => {
            if (name === 'production') return [`${value.toFixed(2)} Wh`, '생산량'];
            if (name === 'consumption') return [`${value.toFixed(2)} Wh`, '소비량'];
            if (name === 'essPower') {
              if (value < 0) return [`${Math.abs(value).toFixed(2)} Wh (방전)`, 'ESS 방전량'];
              return [`${value.toFixed(2)} Wh (충전)`, 'ESS 충전량'];
            }
            return [value, name];
          }}
          labelFormatter={(label) => `${label} 시간대`}
        />
        <Legend />
        <Bar dataKey="production" name="생산량" fill={COLORS.green[0]} />
        <Bar dataKey="consumption" name="소비량" fill={COLORS.orange[0]} />
        <Bar dataKey="essPower" name="ESS 전력">
          {hourlyPlanData.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={entry.isCharging ? COLORS.green[2] : (entry.isDischarging ? COLORS.blue[2] : COLORS.idle)} 
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  </div>
</div>
        
        <div className="bg-white p-6 rounded shadow">
          <h3 className="text-lg font-semibold mb-4">충방전 모드 타임라인</h3>
          <div className="overflow-x-auto">
            <div className="min-w-full grid grid-cols-24 gap-1">
              {hourlyPlanData.map((plan, index) => (
                <div 
                  key={index}
                  className={`p-2 text-center text-xs h-16 flex flex-col justify-center ${
                    plan.isCharging 
                      ? 'bg-green-100 text-green-800'
                      : plan.isDischarging
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <div className="font-bold">{plan.hour}:00</div>
                  <div>{plan.essMode}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-4 flex justify-center gap-4">
            <div className="flex items-center">
              <div className="w-4 h-4 bg-green-100 mr-1"></div>
              <span className="text-xs">충전</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-blue-100 mr-1"></div>
              <span className="text-xs">방전</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-gray-100 mr-1"></div>
              <span className="text-xs">유휴</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // ESS 시뮬레이션 대시보드 렌더링
  const renderEssSimulationDashboard = () => {
    if (!simulationResult) {
      return (
        <div className="text-center py-8 text-gray-500">
          <p>ESS 시뮬레이션 결과를 불러오는 중입니다. '새로고침' 버튼을 눌러주세요.</p>
        </div>
      );
    }

    // 시간별 결과 데이터 변환
    const hourlyResultData = simulationResult.hourly_results.map(result => ({
      hour: result.hour,
      label: formatHour(result.hour),
      isNighttime: result.is_nighttime,
      powerProduction: result.power_production,
      startSoc: result.start_soc,
      endSoc: result.end_soc,
      socChange: result.soc_change
    }));

    return (
      <div className="space-y-6">
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-xl font-semibold mb-4">ESS 시뮬레이션 결과 요약</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded">
              <h3 className="text-sm font-medium text-gray-600">위치</h3>
              <p className="text-lg font-bold text-blue-700">{simulationResult.location}</p>
            </div>
            
            <div className="bg-green-50 p-4 rounded">
              <h3 className="text-sm font-medium text-gray-600">총 전력 생산량</h3>
              <p className="text-lg font-bold text-green-700">{simulationResult.total_power_production.toFixed(2)} Wh</p>
            </div>
            
            <div className="bg-purple-50 p-4 rounded">
              <h3 className="text-sm font-medium text-gray-600">총 방전량</h3>
              <p className="text-lg font-bold text-purple-700">{simulationResult.total_discharge_power.toFixed(2)} Wh</p>
            </div>
            
            <div className="bg-indigo-50 p-4 rounded">
              <h3 className="text-sm font-medium text-gray-600">SOC 변화</h3>
              <p className="text-lg font-bold text-indigo-700">
                {simulationResult.initial_soc.toFixed(1)}% → {simulationResult.final_soc.toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded shadow">
          <h3 className="text-lg font-semibold mb-4">시간별 SOC 변화</h3>
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={hourlyResultData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="label"
                  tick={{ fontSize: 12 }}
                  interval={2}
                  label={{ value: '시간', position: 'insideBottom', offset: -5 }}
                />
                <YAxis 
                  yAxisId="left"
                  label={{ value: 'SOC (%)', angle: -90, position: 'insideLeft' }}
                  domain={[0, 100]}
                />
                <YAxis 
                  yAxisId="right"
                  orientation="right"
                  label={{ value: '전력량 (Wh)', angle: 90, position: 'insideRight' }}
                  domain={[0, 'auto']}
                />
                <Tooltip 
                  formatter={(value, name) => {
                    if (name === 'endSoc') return [`${value.toFixed(1)}%`, 'SOC'];
                    if (name === 'powerProduction') return [`${value.toFixed(2)} Wh`, '전력 생산량'];
                    return [value, name];
                  }}
                  labelFormatter={(label) => `${label} 시간대`}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="endSoc" 
                  name="SOC" 
                  yAxisId="left"
                  stroke="#8884d8" 
                  activeDot={{ r: 8 }} 
                />
                <Line 
                  type="monotone" 
                  dataKey="powerProduction" 
                  name="전력 생산량" 
                  yAxisId="right"
                  stroke="#82ca9d" 
                />
                <ReferenceLine 
                  y={80} 
                  yAxisId="left"
                  label="80% (충전 적정선)" 
                  stroke="green" 
                  strokeDasharray="3 3"
                />
                <ReferenceLine 
                  y={20} 
                  yAxisId="left"
                  label="20% (방전 경고선)" 
                  stroke="red" 
                  strokeDasharray="3 3"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded shadow">
            <h3 className="text-lg font-semibold mb-4">SOC 변화량</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={hourlyResultData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="label"
                    tick={{ fontSize: 12 }}
                    interval={2}
                  />
                  <YAxis 
                    label={{ value: 'SOC 변화 (%p)', angle: -90, position: 'insideLeft' }}
                    domain={['auto', 'auto']}
                  />
                  <Tooltip 
                    formatter={(value, name) => {
                      if (name === 'socChange') {
                        const prefix = value >= 0 ? '+' : '';
                        return [`${prefix}${value.toFixed(1)}%`, 'SOC 변화'];
                      }
                      return [value, name];
                    }}
                  />
                  <Bar 
                    dataKey="socChange" 
                    name="SOC 변화"
                    fill={(data) => (data.socChange >= 0 ? COLORS.green[1] : COLORS.blue[1])}
                  />
                  <ReferenceLine y={0} stroke="#000" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded shadow">
            <h3 className="text-lg font-semibold mb-4">주/야간 모드</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={hourlyResultData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="label"
                    tick={{ fontSize: 12 }}
                    interval={2}
                  />
                  <YAxis 
                    label={{ value: 'SOC (%)', angle: -90, position: 'insideLeft' }}
                    domain={[0, 100]}
                  />
                  <Tooltip />
                  <Area 
                    type="monotone" 
                    dataKey="endSoc" 
                    name="SOC" 
                    stroke="#8884d8"
                    fill={(data) => (data.isNighttime ? "#b3a7ff" : "#ffe8a3")}
                  />
                  {hourlyResultData.map((data, index) => (
                    <ReferenceLine 
                      key={index}
                      x={data.label} 
                      stroke={data.isNighttime ? "#6c5ce7" : "#fdcb6e"} 
                      strokeOpacity={0.3}
                      strokeWidth={8}
                    />
                  ))}
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 flex justify-center gap-4">
              <div className="flex items-center">
                <div className="w-4 h-4 bg-yellow-200 mr-1"></div>
                <span className="text-xs">주간 (충전)</span>
              </div>
              <div className="flex items-center">
                <div className="w-4 h-4 bg-indigo-200 mr-1"></div>
                <span className="text-xs">야간 (방전)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // 메인 대시보드 렌더링
  return (
    <div className="flex flex-col p-6 max-w-6xl mx-auto bg-gray-50 min-h-screen">
      <h1 className="text-5xl font-bold mb-4 text-center text-gray-800">ESS 대시보드</h1>
      <p className="text-xl text-center text-gray-600 mb-6">배터리 충방전 및 관리 시스템</p>
      
      {renderTabs()}
      {renderControls()}
      
      {error && (
        <div className="mb-6 p-4 bg-red-100 text-red-700 rounded">
          <p className="font-semibold">오류 발생:</p>
          <p>{error}</p>
        </div>
      )}
      
      {loading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-blue-600">데이터 로딩 중...</p>
        </div>
      ) : (
        <>
          {activeTab === 'status' && renderBatteryStatusDashboard()}
          {activeTab === 'realtime' && renderRealtimeEssDashboard()}
          {activeTab === 'schedule' && renderDailyScheduleDashboard()}
          {activeTab === 'simulation' && renderEssSimulationDashboard()}
        </>
      )}
      
      <div className="mt-8 text-center text-gray-500 text-sm">
        <p>ESS 대시보드 v1.0.0 &copy; {new Date().getFullYear()}</p>
      </div>
    </div>
  );
};

export default ESSDashboard;