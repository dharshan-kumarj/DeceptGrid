import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import HoneypotPanel from '../components/HoneypotPanel.jsx'
import MeterStatusPanel from '../components/MeterStatusPanel.jsx'
import AuthLogPanel from '../components/AuthLogPanel.jsx'

const API = 'http://localhost:8001'

export default function Dashboard() {
  const navigate = useNavigate()
  const [clock, setClock] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
  const [isMockMode, setIsMockMode] = useState(false)

  const behaviourScore = localStorage.getItem('gridshield_behaviour_score') || '—'
  const riskLabel = localStorage.getItem('gridshield_risk_label') || 'UNKNOWN'

  // Live clock
  useEffect(() => {
    const tick = () => {
      const now = new Date()
      setClock(
        now.toLocaleTimeString('en-GB', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        })
      )
    }
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [])

  // Auto-refresh panels every 5 seconds
  useEffect(() => {
    const id = setInterval(() => {
      setRefreshKey((k) => k + 1)
    }, 5000)
    return () => clearInterval(id)
  }, [])

  // Check for mock data mode
  useEffect(() => {
    const check = async () => {
      try {
        const res = await axios.get(`${API}/logs/honeypot?limit=200`)
        if (res.data && res.data.length < 5) {
          setIsMockMode(true)
        } else {
          setIsMockMode(false)
        }
      } catch {
        setIsMockMode(true)
      }
    }
    check()
  }, [refreshKey])

  const handleLogout = () => {
    localStorage.removeItem('gridshield_token')
    localStorage.removeItem('gridshield_behaviour_score')
    localStorage.removeItem('gridshield_risk_label')
    navigate('/')
  }

  const badgeClass =
    riskLabel === 'NORMAL'
      ? 'normal'
      : riskLabel === 'SUSPICIOUS'
      ? 'suspicious'
      : 'bot'

  return (
    <div className="dashboard-page">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <h1>GRIDSHIELD SOC // ENGINEER DASHBOARD</h1>
        </div>
        <div className="header-center">
          <span className="live-clock">{clock}</span>
        </div>
        <div className="header-right">
          <span className={`behaviour-badge ${badgeClass}`}>
            SCORE: {behaviourScore} — {riskLabel}
          </span>
          <button className="logout-btn" onClick={handleLogout}>
            LOGOUT
          </button>
        </div>
      </header>

      {/* Mock Data Banner */}
      {isMockMode && (
        <div className="mock-banner">
          ⚠ MOCK DATA MODE — Fewer than 5 log entries detected
        </div>
      )}

      {/* Dashboard Grid */}
      <div className="dashboard-grid">
        <HoneypotPanel refreshKey={refreshKey} />
        <MeterStatusPanel refreshKey={refreshKey} />
        <AuthLogPanel refreshKey={refreshKey} />
      </div>
    </div>
  )
}

