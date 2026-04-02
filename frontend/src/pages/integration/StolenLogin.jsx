import React, { useState } from 'react';
import { API, apiCall } from '../../constants/api.ts';

/**
 * StolenLogin.jsx - Attacker Stolen Credentials Page 5
 * Person C - Stolen credential login attempt with behavioral analysis
 */

const StolenLogin = () => {
  // Stolen credentials (pre-filled)
  const stolenCredentials = {
    username: 'engineer_01',
    password: 'grid@2024'
  };

  const [typingSpeed, setTypingSpeed] = useState(0.24); // Default slow typing (suspicious)
  const [loginStatus, setLoginStatus] = useState('idle'); // idle, attempting, blocked, success
  const [behaviorScore, setBehaviorScore] = useState(0);
  const [blockReason, setBlockReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Convert slider value (0-1) to typing speed description
  const getSpeedDescription = (speed) => {
    if (speed < 0.3) return 'Very Slow (Suspicious)';
    if (speed < 0.5) return 'Slow';
    if (speed < 0.7) return 'Normal';
    if (speed < 0.9) return 'Fast';
    return 'Very Fast';
  };

  // Convert typing speed to characters per second for display
  const getCharPerSec = (speed) => {
    return (speed * 5).toFixed(1); // Scale to reasonable chars/sec
  };

  const handleLogin = async () => {
    setLoading(true);
    setError('');
    setLoginStatus('attempting');
    setBehaviorScore(0);
    setBlockReason('');

    try {
      // Simulate typing delay based on speed
      const typingDelay = Math.max(500, 2000 * (1 - typingSpeed));
      await new Promise(resolve => setTimeout(resolve, typingDelay));

      // Make API call to stolen login endpoint
      const response = await apiCall(API.STOLEN_LOGIN, {
        method: 'POST',
        body: JSON.stringify({
          username: stolenCredentials.username,
          password: stolenCredentials.password,
          typing_speed: typingSpeed
        })
      });

      setBehaviorScore(response.behavior_score);
      setBlockReason(response.reason);

      if (response.status === 'blocked') {
        setLoginStatus('blocked');
      } else {
        setLoginStatus('success');
      }

    } catch (error) {
      setError('Network error. Cannot reach SCADA system.');
      setLoginStatus('idle');
    } finally {
      setLoading(false);
    }
  };

  const resetAttempt = () => {
    setLoginStatus('idle');
    setBehaviorScore(0);
    setBlockReason('');
    setError('');
  };

  const getStatusDisplay = () => {
    switch (loginStatus) {
      case 'attempting':
        return (
          <div className="bg-yellow-900/50 border border-yellow-600 text-yellow-300 px-4 py-3 rounded-md flex items-center animate-pulse">
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-yellow-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <div>
              <div className="font-semibold">Attempting SCADA login...</div>
              <div className="text-sm opacity-80">Analyzing behavioral patterns</div>
            </div>
          </div>
        );

      case 'blocked':
        return (
          <div className="space-y-4">
            <div className="bg-red-900/50 border-2 border-red-500 text-red-200 px-6 py-4 rounded-lg">
              <div className="flex items-center mb-3">
                <span className="text-3xl mr-3">❌</span>
                <div>
                  <div className="text-xl font-bold text-red-400">ACCESS DENIED</div>
                  <div className="text-lg">Behavioral Score: <span className="font-mono font-bold">{behaviorScore}%</span></div>
                </div>
              </div>
              <div className="bg-red-800/50 px-4 py-2 rounded border border-red-600">
                <div className="text-sm font-semibold text-red-300 mb-1">Detection Reason:</div>
                <div className="font-mono text-red-200">{blockReason}</div>
              </div>
            </div>

            <div className="bg-gray-800 border border-gray-600 rounded-lg p-4">
              <h4 className="text-sm font-bold text-gray-400 mb-2">BEHAVIORAL ANALYSIS RESULTS:</h4>
              <div className="text-xs text-gray-300 space-y-1 font-mono">
                <div>• Typing Speed: {getCharPerSec(typingSpeed)} chars/sec (Expected: >3.0 chars/sec)</div>
                <div>• Confidence Level: HIGH</div>
                <div>• Risk Assessment: STOLEN CREDENTIALS DETECTED</div>
                <div>• Action Taken: Login blocked, incident logged</div>
              </div>
            </div>

            <button
              onClick={resetAttempt}
              className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-4 rounded-md transition duration-200"
            >
              Try Different Approach
            </button>
          </div>
        );

      case 'success':
        return (
          <div className="space-y-4">
            <div className="bg-green-900/50 border-2 border-green-500 text-green-200 px-6 py-4 rounded-lg text-center">
              <div className="text-3xl mb-2">✅</div>
              <div className="text-xl font-bold text-green-400 mb-2">LOGIN SUCCESSFUL</div>
              <div className="text-lg">Behavioral Score: <span className="font-mono font-bold">{behaviorScore}%</span></div>
              <div className="text-sm mt-2 opacity-90">Bypassed security detection</div>
            </div>

            <button
              onClick={resetAttempt}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-md transition duration-200"
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
          <div className="text-xs text-gray-500">attacker@deceptgrid:~$ ./credential_hijack.py</div>
        </div>

        {/* Main Content */}
        <div className="bg-gray-800 border-l border-r border-b border-red-600 rounded-b-lg p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-red-400 mb-2 flex items-center justify-center">
              <svg className="w-8 h-8 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              SCADA Dashboard Login Attempt
            </h1>
            <div className="text-lg text-red-300">
              Using <span className="font-mono bg-red-900/30 px-2 py-1 rounded">STOLEN CREDENTIALS</span>
            </div>
          </div>

          {/* Stolen Credentials Display */}
          <div className="bg-gray-900 border border-red-600 rounded-lg p-6 mb-6">
            <h3 className="text-xl font-bold text-red-400 mb-4 flex items-center">
              <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              INTERCEPTED CREDENTIALS
            </h3>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-red-300 mb-2">USERNAME</label>
                <div className="bg-black border border-red-600 text-green-400 px-4 py-3 rounded font-mono text-lg">
                  {stolenCredentials.username}
                </div>
              </div>
              <div>
                <label className="block text-sm font-semibold text-red-300 mb-2">PASSWORD</label>
                <div className="bg-black border border-red-600 text-green-400 px-4 py-3 rounded font-mono text-lg">
                  {stolenCredentials.password}
                </div>
              </div>
            </div>
          </div>

          {/* Typing Speed Simulation */}
          <div className="bg-gray-900 border border-yellow-600 rounded-lg p-6 mb-6">
            <h3 className="text-xl font-bold text-yellow-400 mb-4 flex items-center">
              <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              BEHAVIORAL SIMULATION
            </h3>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-yellow-300 font-semibold">Typing Speed Simulation</label>
                  <div className="text-right">
                    <div className="text-lg font-mono text-yellow-400">{getCharPerSec(typingSpeed)} chars/sec</div>
                    <div className="text-sm text-yellow-600">{getSpeedDescription(typingSpeed)}</div>
                  </div>
                </div>

                <div className="relative">
                  <input
                    type="range"
                    min="0.1"
                    max="1.0"
                    step="0.05"
                    value={typingSpeed}
                    onChange={(e) => setTypingSpeed(parseFloat(e.target.value))}
                    className="w-full h-3 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                    disabled={loading || loginStatus !== 'idle'}
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Fast</span>
                    <span>Slow</span>
                  </div>
                </div>

                <div className="text-xs text-yellow-500 mt-2 bg-yellow-900/20 px-3 py-2 rounded border border-yellow-800">
                  <strong>Simulation:</strong> Slower typing suggests unfamiliarity with credentials (stolen),
                  faster typing indicates legitimate user familiarity
                </div>
              </div>
            </div>
          </div>

          {/* Login Button */}
          {loginStatus === 'idle' && (
            <div className="mb-6">
              {error && (
                <div className="bg-red-900/50 border border-red-600 text-red-300 px-4 py-2 rounded text-sm mb-4">
                  ⚠️ {error}
                </div>
              )}

              <button
                onClick={handleLogin}
                disabled={loading}
                className="w-full bg-red-700 hover:bg-red-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-4 px-6 rounded-lg transition duration-200 text-lg flex items-center justify-center"
              >
                <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                </svg>
                Login with Stolen Password
              </button>
            </div>
          )}

          {/* Status Display */}
          {loginStatus !== 'idle' && (
            <div className="mb-6">
              {getStatusDisplay()}
            </div>
          )}

          {/* Attack Info */}
          <div className="bg-black/50 border border-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-bold text-gray-400 mb-2">ATTACK DETAILS:</h4>
            <div className="text-xs text-gray-500 space-y-1 font-mono">
              <div>• Method: Credential Theft & Behavioral Spoofing</div>
              <div>• Target: SCADA Authentication System</div>
              <div>• Detection: Behavioral Biometric Analysis</div>
              <div>• Evasion: Typing Speed Manipulation</div>
              <div>• Status: All attempts logged by security system</div>
            </div>
          </div>
        </div>
      </div>

      {/* CSS for slider styling */}
      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          height: 20px;
          width: 20px;
          border-radius: 50%;
          background: #ef4444;
          cursor: pointer;
          border: 2px solid #dc2626;
        }

        .slider::-moz-range-thumb {
          height: 20px;
          width: 20px;
          border-radius: 50%;
          background: #ef4444;
          cursor: pointer;
          border: 2px solid #dc2626;
        }
      `}</style>
    </div>
  );
};

export default StolenLogin;