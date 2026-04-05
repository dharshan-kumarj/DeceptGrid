import { useState, useEffect } from 'react'
import axios from 'axios'

const API = 'http://localhost:8001'

export default function AuthLogPanel({ refreshKey }) {
  const [blocked, setBlocked] = useState([])
  const [allowed, setAllowed] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    const fetchData = async () => {
      try {
        const res = await axios.get(`${API}/logs/auth?limit=30`)
        if (!cancelled) {
          setBlocked(res.data.blocked || [])
          setAllowed(res.data.allowed || [])
          setLoading(false)
        }
      } catch {
        if (!cancelled) setLoading(false)
      }
    }
    fetchData()
    return () => { cancelled = true }
  }, [refreshKey])

  return (
    <div className="panel glow-danger">
      <div className="panel-header">
        <div className="panel-title">🔐 AUTH LOG</div>
        <div className="panel-subtitle">AUTHENTICATION EVENTS — BLOCKED VS ALLOWED</div>
      </div>
      <div className="panel-body">
        {loading ? (
          <div className="honeypot-idle">LOADING AUTH DATA...</div>
        ) : (
          <div className="auth-columns">
            {/* BLOCKED */}
            <div className="auth-column">
              <div className="auth-column-header">
                <span className="auth-column-title blocked">ACCESS DENIED</span>
                <span className="auth-count-badge blocked">{blocked.length}</span>
              </div>
              <div className="auth-list">
                {blocked.length === 0 ? (
                  <div className="honeypot-idle" style={{ padding: '20px 0' }}>NO BLOCKED ENTRIES</div>
                ) : (
                  blocked.map((entry, i) => (
                    <div key={`b-${entry.time}-${entry.ip}-${i}`} className="auth-entry blocked">
                      <span className="entry-time">{entry.time}</span>
                      <span className="entry-ip">{entry.ip}</span>
                      <span className="entry-type">{entry.type}</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* ALLOWED */}
            <div className="auth-column">
              <div className="auth-column-header">
                <span className="auth-column-title allowed">ACCESS GRANTED</span>
                <span className="auth-count-badge allowed">{allowed.length}</span>
              </div>
              <div className="auth-list">
                {allowed.length === 0 ? (
                  <div className="honeypot-idle" style={{ padding: '20px 0' }}>NO ALLOWED ENTRIES</div>
                ) : (
                  allowed.map((entry, i) => (
                    <div key={`a-${entry.time}-${entry.ip}-${i}`} className="auth-entry allowed">
                      <span className="entry-time">{entry.time}</span>
                      <span className="entry-ip">{entry.ip}</span>
                      <span className="entry-type">{entry.type}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
