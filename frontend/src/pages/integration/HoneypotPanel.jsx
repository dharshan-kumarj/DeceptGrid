import React from 'react';
import { useHoneypotLogs, useAttackLogs } from '../../hooks/useAutoRefresh';

/**
 * HoneypotPanel.jsx - Sample Engineer Dashboard Panel
 * Person C - Reference implementation for Person B's dashboard integration
 *
 * NOTE: This is a SAMPLE/REFERENCE file for Person B to use when building
 * their engineer dashboard. Person B should integrate the auto-refresh logic
 * into their actual HoneypotPanel component.
 */

const HoneypotPanel = () => {
  // Auto-refresh honeypot logs every 2.5 seconds
  const { logs: honeypotLogs, loading: honeypotLoading, error: honeypotError } = useHoneypotLogs(2500);

  // Auto-refresh attack logs every 2.5 seconds
  const { logs: attackLogs, loading: attackLoading, error: attackError } = useAttackLogs(2500);

  const formatTime = (timeStr) => {
    return timeStr || new Date().toLocaleTimeString().slice(0, 5);
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'HIGH': return 'text-red-600 bg-red-100';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-100';
      case 'LOW': return 'text-blue-600 bg-blue-100';
      case 'CRITICAL': return 'text-purple-600 bg-purple-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 max-w-6xl mx-auto">
      <div className="border-b border-gray-200 pb-4 mb-6">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center">
          <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium mr-3">
            ENGINEER
          </span>
          Security Monitoring Dashboard
        </h2>
        <p className="text-gray-600 mt-2">Real-time monitoring of honeypot and security events</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Honeypot Activity Panel */}
        <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
          <h3 className="text-xl font-semibold text-blue-800 mb-4 flex items-center">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Honeypot Activity
            {honeypotLoading && <span className="ml-2 text-sm animate-pulse">●</span>}
          </h3>

          {honeypotError && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded text-sm mb-4">
              ⚠️ {honeypotError}
            </div>
          )}

          <div className="space-y-3 max-h-80 overflow-y-auto">
            {honeypotLogs.length > 0 ? (
              honeypotLogs.map((log, index) => (
                <div key={index} className="bg-white border border-blue-200 rounded p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-sm text-blue-600">{formatTime(log.time)}</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(log.severity)}`}>
                      {log.severity || 'INFO'}
                    </span>
                  </div>
                  <div className="text-sm">
                    <div className="font-semibold text-gray-800">{log.type || 'Honeypot Activity'}</div>
                    <div className="text-gray-600">IP: {log.ip || 'unknown'} → Target: {log.target || 'honeypot'}</div>
                    <div className="text-gray-500 mt-1">{log.details || log.message || 'Activity detected'}</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500 py-8">
                {honeypotLoading ? 'Loading honeypot logs...' : 'No honeypot activity detected'}
              </div>
            )}
          </div>
        </div>

        {/* Attack Detection Panel */}
        <div className="bg-red-50 rounded-lg p-6 border border-red-200">
          <h3 className="text-xl font-semibold text-red-800 mb-4 flex items-center">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            Attack Detection
            {attackLoading && <span className="ml-2 text-sm animate-pulse">●</span>}
          </h3>

          {attackError && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded text-sm mb-4">
              ⚠️ {attackError}
            </div>
          )}

          <div className="space-y-3 max-h-80 overflow-y-auto">
            {attackLogs.length > 0 ? (
              attackLogs.map((log, index) => (
                <div key={index} className="bg-white border border-red-200 rounded p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-sm text-red-600">{formatTime(log.time)}</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(log.severity)}`}>
                      {log.severity}
                    </span>
                  </div>
                  <div className="text-sm">
                    <div className="font-semibold text-gray-800">{log.type}</div>
                    <div className="text-gray-600">IP: {log.ip} → Target: {log.target}</div>
                    <div className="text-gray-500 mt-1">{log.details}</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500 py-8">
                {attackLoading ? 'Loading attack logs...' : 'No attacks detected'}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div className="mt-8 bg-gray-50 rounded-lg p-4 border border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
              <span className="text-gray-600">Live Monitoring Active</span>
            </div>
            <div className="text-gray-500">
              |
            </div>
            <div className="text-gray-500">
              Refresh: 2.5s
            </div>
          </div>
          <div className="text-gray-500">
            Total Events: {honeypotLogs.length + attackLogs.length}
          </div>
        </div>
      </div>

      {/* Integration Notes for Person B */}
      <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h4 className="text-sm font-bold text-yellow-800 mb-2">Integration Notes for Person B:</h4>
        <ul className="text-xs text-yellow-700 space-y-1">
          <li>• Use the <code className="bg-yellow-200 px-1 rounded">useHoneypotLogs()</code> and <code className="bg-yellow-200 px-1 rounded">useAttackLogs()</code> hooks from <code>hooks/useAutoRefresh.js</code></li>
          <li>• Auto-refresh is set to 2.5 seconds - adjust as needed for performance</li>
          <li>• The hooks handle loading states, errors, and cleanup automatically</li>
          <li>• Integrate this logic into your actual HoneypotPanel component</li>
          <li>• This file can be deleted once integrated into your dashboard</li>
        </ul>
      </div>
    </div>
  );
};

export default HoneypotPanel;