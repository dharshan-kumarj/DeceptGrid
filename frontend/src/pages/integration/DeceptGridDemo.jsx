import React, { useState } from 'react';
import Steg from './Steg';
import Injection from './Injection';
import StolenLogin from './StolenLogin';
import HoneypotPanel from './HoneypotPanel';

/**
 * DeceptGridDemo.jsx - Combined Demo Page
 * Person C - Demonstration of all integration components
 */

const DeceptGridDemo = () => {
  const [activeView, setActiveView] = useState('steg');
  const [userRole, setUserRole] = useState('engineer'); // 'engineer' or 'attacker'

  const engineerViews = [
    { id: 'steg', name: 'Steganography', icon: '🔒' },
    { id: 'monitoring', name: 'Security Monitoring', icon: '🛡️' }
  ];

  const attackerViews = [
    { id: 'injection', name: 'Data Injection', icon: '⚡' },
    { id: 'stolen-login', name: 'Credential Theft', icon: '🔑' }
  ];

  const currentViews = userRole === 'engineer' ? engineerViews : attackerViews;

  const renderComponent = () => {
    if (userRole === 'engineer') {
      switch (activeView) {
        case 'steg': return <Steg />;
        case 'monitoring': return <HoneypotPanel />;
        default: return <Steg />;
      }
    } else {
      switch (activeView) {
        case 'injection': return <Injection />;
        case 'stolen-login': return <StolenLogin />;
        default: return <Injection />;
      }
    }
  };

  const handleRoleSwitch = (newRole) => {
    setUserRole(newRole);
    // Set default view for each role
    if (newRole === 'engineer') {
      setActiveView('steg');
    } else {
      setActiveView('injection');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Role Switcher Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">DeceptGrid</h1>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${userRole === 'engineer'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
                }`}>
                {userRole === 'engineer' ? '🛡️ ENGINEER MODE' : '🔥 ATTACKER MODE'}
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleRoleSwitch('engineer')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${userRole === 'engineer'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
              >
                Engineer
              </button>
              <button
                onClick={() => handleRoleSwitch('attacker')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${userRole === 'attacker'
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
              >
                Attacker
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className={`${userRole === 'engineer' ? 'bg-green-50' : 'bg-gray-900'
        } border-b ${userRole === 'engineer' ? 'border-green-200' : 'border-gray-700'
        }`}>
        <div className="max-w-7xl mx-auto px-4">
          <nav className="flex space-x-8">
            {currentViews.map((view) => (
              <button
                key={view.id}
                onClick={() => setActiveView(view.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${activeView === view.id
                    ? userRole === 'engineer'
                      ? 'border-green-500 text-green-700'
                      : 'border-red-500 text-red-400'
                    : userRole === 'engineer'
                      ? 'border-transparent text-green-600 hover:text-green-700 hover:border-green-300'
                      : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-500'
                  }`}
              >
                <span className="flex items-center space-x-2">
                  <span>{view.icon}</span>
                  <span>{view.name}</span>
                </span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className={`${userRole === 'attacker' ? 'p-0' : 'p-6'
        }`}>
        {renderComponent()}
      </div>

      {/* Demo Instructions */}
      <div className="fixed bottom-4 right-4 max-w-sm">
        <div className="bg-white rounded-lg shadow-lg border p-4 text-sm">
          <h4 className="font-bold text-gray-800 mb-2">💡 Demo Instructions</h4>
          <ul className="text-gray-600 space-y-1 text-xs">
            <li>• Switch between Engineer/Attacker modes</li>
            <li>• <strong>Engineer:</strong> Hide messages, monitor attacks</li>
            <li>• <strong>Attacker:</strong> Inject data, steal credentials</li>
            <li>• All actions are logged and monitored</li>
            <li>• Backend must be running on localhost:8000</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default DeceptGridDemo;