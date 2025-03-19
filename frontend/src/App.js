import React from 'react';
import PowerDashboard from './PowerDashboard';

// API 기본 URL 설정 (환경변수 사용)
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

const App = () => {
  return (
    <div className="flex flex-col p-6 max-w-6xl mx-auto bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold mb-2 text-center text-gray-800">전력 발전량 통합 시스템</h1>
      <p className="text-center text-gray-600 mb-6">기상청 API 연동 인천광역시 미추홀구 용현1.4동 날씨 기반</p>
      
      <PowerDashboard />
      
      <div className="mt-8 text-center text-gray-500 text-sm">
        <p>전력 발전량 통합 시스템 v2.0.0 &copy; {new Date().getFullYear()} - 기상청 단기예보 API 활용</p>
      </div>
    </div>
  );
};

export default App;