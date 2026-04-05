import { useState, useEffect } from 'react'
import axios from 'axios'

const API = 'http://localhost:8001'

export default function MeterStatusPanel({ refreshKey }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    const fetchData = async () => {
      try {
        const res = await axios.get(`${API}/logs/meter-status`)
        if (!cancelled) {
          setData(res.data)
          setLoading(false)
        }
      } catch {
        if (!cancelled) setLoading(false)
      }
    }
    fetchData()
    return () => { cancelled = true }
  }, [refreshKey])

  if (loading || !data) {
    return (
      <div className="panel glow-warning">
        <div className="panel-header">
          <div className="panel-title">⚡ METER STATUS</div>
          <div className="panel-subtitle">REAL VS HONEYPOT COMPARISON</div>
        </div>
        <div className="panel-body">
          <div className="honeypot-idle">LOADING STATUS...</div>
        </div>
      </div>
    )
  }

  const { real_meter, fake_meter } = data
  const realIsAttacked = real_meter.status === 'UNDER_ATTACK'
  const fakeIsActive = fake_meter.status === 'UNDER_ATTACK'

  const countClass = (count) => {
    if (count >= 5) return 'danger'
    if (count >= 2) return 'warning'
    return 'safe'
  }

  return (
    <div className="panel glow-warning">
      <div className="panel-header">
        <div className="panel-title">⚡ METER STATUS</div>
        <div className="panel-subtitle">REAL VS HONEYPOT COMPARISON</div>
      </div>
      <div className="panel-body">
        <div className="meter-cards">
          {/* REAL METER */}
          <div className={`meter-card ${realIsAttacked ? 'real-attack' : 'real-secure'}`}>
            <div className="meter-card-label">REAL METER — RealMeter_01</div>
            <div className="status-indicator">
              <div className={`status-dot ${realIsAttacked ? 'under-attack' : 'secure'}`} />
              <span className={`status-text ${realIsAttacked ? 'under-attack' : 'secure'}`}>
                {real_meter.status === 'UNDER_ATTACK' ? 'UNDER ATTACK' : 'SECURE'}
              </span>
            </div>
            <div className={`meter-attack-count ${countClass(real_meter.attack_count)}`}>
              {real_meter.attack_count}
            </div>
            <div className="meter-stat">
              <span className="meter-stat-label">ATTACKS</span>
              <span className="meter-stat-value">{real_meter.attack_count}</span>
            </div>
            <div className="meter-stat">
              <span className="meter-stat-label">LAST IP</span>
              <span className="meter-stat-value">{real_meter.last_ip || '—'}</span>
            </div>
            <div className="meter-stat">
              <span className="meter-stat-label">LAST TIME</span>
              <span className="meter-stat-value">{real_meter.last_time || '—'}</span>
            </div>
          </div>

          {/* FAKE METER / HONEYPOT */}
          <div className={`meter-card ${fakeIsActive ? 'fake-active' : 'fake-idle'}`}>
            <div className="meter-card-label">FAKE METER — HONEYPOT</div>
            <div className="status-indicator">
              <div className={`status-dot ${fakeIsActive ? 'bait-active' : 'idle'}`} />
              <span className={`status-text ${fakeIsActive ? 'bait-active' : 'idle'}`}>
                {fakeIsActive ? 'ACTIVE BAIT' : 'IDLE'}
              </span>
            </div>
            <div className={`meter-attack-count ${countClass(fake_meter.attack_count)}`}>
              {fake_meter.attack_count}
            </div>
            <div className="meter-stat">
              <span className="meter-stat-label">ATTACKS</span>
              <span className="meter-stat-value">{fake_meter.attack_count}</span>
            </div>
            <div className="meter-stat">
              <span className="meter-stat-label">LAST IP</span>
              <span className="meter-stat-value">{fake_meter.last_ip || '—'}</span>
            </div>
            <div className="meter-stat">
              <span className="meter-stat-label">LAST TYPE</span>
              <span className="meter-stat-value">{fake_meter.last_type || '—'}</span>
            </div>
            <div className="meter-stat">
              <span className="meter-stat-label">LAST TIME</span>
              <span className="meter-stat-value">{fake_meter.last_time || '—'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
