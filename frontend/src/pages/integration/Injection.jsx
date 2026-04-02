import React, { useState } from 'react';
import { API, apiCall } from '../../constants/api.ts';

/**
 * Injection.jsx - Attacker Data Tampering Page 4
 * Person C - False data injection attack simulation for attackers
 */

const Injection = () => {
  const [targetValue, setTargetValue] = useState('');
  const [attackStatus, setAttackStatus] = useState('idle'); // idle, sending, accepted, success
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Current meter reading (simulated)
  const currentReading = '220V';
  const targetMeter = 'Meter_01';

  const handleInject = async () => {
    if (!targetValue.trim()) {
      setError('Please enter a value to inject');
      return;
    }

    setLoading(true);
    setError('');
    setAttackStatus('sending');

    try {
      // Simulate sending delay
      await new Promise(resolve => setTimeout(resolve, 500));

      // Make API call to inject attack
      const response = await apiCall(API.INJECT, {
        method: 'POST',
        body: JSON.stringify({
          target: targetMeter,
          value: targetValue.trim(),
          attacker_ip: '192.168.1.45' // Simulated attacker IP
        })
      });

      setAttackStatus('accepted');

      // Simulate processing delay
      await new Promise(resolve => setTimeout(resolve, 500));

      setAttackStatus('success');

    } catch (error) {
      setError('Attack failed. Network error or backend unavailable.');
      setAttackStatus('idle');
    } finally {
      setLoading(false);
    }
  };

  const resetAttack = () => {
    setAttackStatus('idle');
    setTargetValue('');
    setError('');
  };

  const getStatusDisplay = () => {
    switch (attackStatus) {
      case 'sending':
        return (
          <div className="bg-yellow-900/50 border border-yellow-600 text-yellow-300 px-4 py-3 rounded-md flex items-center animate-pulse">
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-yellow-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Sending tampered data to grid infrastructure...
          </div>
        );
      case 'accepted':
        return (
          <div className="bg-green-900/50 border border-green-600 text-green-300 px-4 py-3 rounded-md flex items-center animate-pulse">
            <svg className="w-5 h-5 mr-3 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Accepted by meter ✅
          </div>
        );
      case 'success':
        return (
          <div className="space-y-3">
            <div className="bg-red-900/50 border border-red-600 text-red-300 px-4 py-3 rounded-md">
              <div className="flex items-center mb-2">
                <span className="text-2xl mr-3">😈</span>
                <span className="font-bold text-lg">Grid now receiving {targetValue}...</span>
              </div>
            </div>
            <div className="bg-red-800/60 border-2 border-red-500 text-red-200 px-6 py-4 rounded-lg text-center">
              <div className="text-2xl font-bold mb-2 text-red-400 animate-bounce">
                🔥 TAMPERING SUCCESSFUL! 🔥
              </div>
              <div className="text-lg font-semibold">
                False reading injection complete
              </div>
              <div className="text-sm mt-2 opacity-90">
                System believes reading is now {targetValue}
              </div>
            </div>
            <button
              onClick={resetAttack}
              className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-4 rounded-md transition duration-200"
            >
              Launch Another Attack
            </button>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-green-400 font-mono p-6">
      <div className="max-w-4xl mx-auto">
        {/* Terminal Header */}
        <div className="bg-black border border-red-600 rounded-t-lg p-4 mb-0">
          <div className="flex items-center space-x-2 mb-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="ml-4 text-red-400 font-bold">TERMINAL</span>
          </div>
          <div className="text-xs text-gray-500">attacker@deceptgrid:~$ ./inject_malicious_data.sh</div>
        </div>

        {/* Main Content */}
        <div className="bg-gray-800 border-l border-r border-b border-red-600 rounded-b-lg p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-red-400 mb-2 flex items-center justify-center">
              <svg className="w-8 h-8 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Data Tampering Panel
            </h1>
            <div className="text-xl text-red-300">
              Target: <span className="font-mono bg-red-900/30 px-2 py-1 rounded">Smart Meter 01</span>
            </div>
          </div>

          {/* Current Status */}
          <div className="bg-gray-900 border border-gray-600 rounded-lg p-6 mb-8">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="text-center">
                <div className="text-sm text-gray-400 mb-2">CURRENT READING</div>
                <div className="text-4xl font-bold text-green-400 bg-black px-6 py-4 rounded border border-green-600 font-mono">
                  {currentReading}
                </div>
                <div className="text-xs text-gray-500 mt-2">Real-time grid voltage</div>
              </div>

              <div className="text-center">
                <div className="text-sm text-gray-400 mb-2">TARGET STATUS</div>
                <div className="text-lg text-red-400 bg-black px-4 py-4 rounded border border-red-600">
                  <div className="flex items-center justify-center space-x-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                    <span>VULNERABLE</span>
                  </div>
                </div>
                <div className="text-xs text-gray-500 mt-2">Ready for injection</div>
              </div>
            </div>
          </div>

          {/* Attack Interface */}
          <div className="bg-gray-900 border border-red-600 rounded-lg p-6 mb-6">
            <h3 className="text-xl font-bold text-red-400 mb-4 flex items-center">
              <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
              </svg>
              INJECTION PARAMETERS
            </h3>

            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                <label className="text-red-300 font-semibold min-w-0 flex-shrink-0">
                  Change to:
                </label>
                <input
                  type="text"
                  value={targetValue}
                  onChange={(e) => setTargetValue(e.target.value)}
                  placeholder="999V"
                  className="flex-1 bg-black border border-red-600 text-red-400 px-4 py-3 rounded font-mono text-lg focus:border-red-400 focus:ring-2 focus:ring-red-900/50 focus:outline-none"
                  disabled={loading || attackStatus !== 'idle'}
                />
              </div>

              {error && (
                <div className="bg-red-900/50 border border-red-600 text-red-300 px-4 py-2 rounded text-sm">
                  ⚠️ {error}
                </div>
              )}

              {attackStatus === 'idle' && (
                <button
                  onClick={handleInject}
                  disabled={loading || !targetValue.trim()}
                  className="w-full bg-red-700 hover:bg-red-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-4 px-6 rounded-lg transition duration-200 text-lg flex items-center justify-center"
                >
                  <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Inject False Reading
                </button>
              )}
            </div>
          </div>

          {/* Attack Status */}
          {attackStatus !== 'idle' && (
            <div className="mb-6">
              {getStatusDisplay()}
            </div>
          )}

          {/* Honeypot Notice (visible in dev/demo) */}
          <div className="bg-gray-700 border border-gray-600 rounded-lg p-4 text-center">
            <div className="text-xs text-gray-400">
              <strong>DEV NOTE:</strong> Real meter untouched — honeypot accepted this attack for monitoring
            </div>
          </div>

          {/* Attack Info */}
          <div className="mt-6 bg-black/50 border border-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-bold text-gray-400 mb-2">ATTACK DETAILS:</h4>
            <div className="text-xs text-gray-500 space-y-1 font-mono">
              <div>• Method: False Data Injection (FDI)</div>
              <div>• Target: Smart Grid Infrastructure / Meter {targetMeter}</div>
              <div>• Attack Vector: Compromised Communication Channel</div>
              <div>• Impact: Grid receives false sensor readings</div>
              <div>• Status: All attacks logged by security monitoring system</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Injection;