import React, { useState } from 'react';
import PowerDashboard from './PowerDashboard';
import ESSDashboard from './ESSDashboard';
import inhaLogo from './images/inha.jpg';

const App = () => {
  const [activeSection, setActiveSection] = useState('power'); // 'power' 또는 'ess'

  return (
    <div className="flex flex-col p-6 max-w-6xl mx-auto min-h-screen relative">
      {/* Semi-transparent container for better readability */}
      <div className="bg-white bg-opacity-90 rounded-lg shadow-lg p-6">
        {/* 인하대학교 로고 추가 - 크기 축소 */}
        <div className="flex justify-center mb-4">
          <img 
            src={inhaLogo} 
            alt="인하대학교 로고" 
            className="w-auto h-auto max-w-sm" 
            // max-w-2xl → max-w-md로 변경 (더 작게)
          />
        </div>
        
        {/* 메인 네비게이션 */}
        <div className="mb-8 flex justify-center">
          <nav className="flex bg-white rounded-lg shadow-md overflow-hidden">
            <button
              className={`px-6 py-3 text-lg font-medium ${
                activeSection === 'power' 
                  ? 'bg-blue-600 text-white' 
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
              onClick={() => setActiveSection('power')}
            >
              전력 대시보드
            </button>
            <button
              className={`px-6 py-3 text-lg font-medium ${
                activeSection === 'ess' 
                  ? 'bg-green-600 text-white' 
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
              onClick={() => setActiveSection('ess')}
            >
              ESS 대시보드
            </button>
          </nav>
        </div>
        
        {/* 활성화된 대시보드 표시 */}
        {activeSection === 'power' ? <PowerDashboard /> : <ESSDashboard />}
        
        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>전력 발전량 통합 시스템 v2.0.0 &copy; {new Date().getFullYear()} - 기상청 단기예보 API 활용</p>
        </div>
      </div>
    </div>
  );
};

export default App;