import { useState, useEffect } from 'react'
import axios from 'axios'

const API = 'http://localhost:8001'

export default function HoneypotPanel({ refreshKey }) {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    const fetchData = async () => {
      try {
        const res = await axios.get(`${API}/logs/honeypot?limit=20`)
        if (!cancelled) {
          setEntries(res.data)
          setLoading(false)
        }
      } catch {
        if (!cancelled) setLoading(false)
      }
    }
    fetchData()
    return () => { cancelled = true }
  }, [refreshKey])

  const getSeverityClass = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'HIGH': return 'high'
      case 'MEDIUM': return 'medium'
      case 'LOW': return 'low'
      default: return 'low'
    }
  }

  return (
    <div className="panel glow-cyan">
      <div className="panel-header">
        <div className="panel-title">⚡ HONEYPOT ATTACK FEED</div>
        <div className="panel-subtitle">LIVE — FAKE METER INTRUSION LOG</div>
      </div>
      <div className="panel-body">
        {loading ? (
          <div className="honeypot-idle">LOADING FEED...</div>
        ) : entries.length === 0 ? (
          <div className="honeypot-idle">NO ATTACKS DETECTED — HONEYPOT IDLE</div>
        ) : (
          <div className="honeypot-feed">
            {entries.map((entry, i) => (
              <div
                key={`${entry.time}-${entry.ip}-${i}`}
                className={`honeypot-entry severity-${getSeverityClass(entry.severity)}`}
              >
                <span className="entry-time">{entry.time}</span>
                <span className="entry-ip">{entry.ip}</span>
                <span className="entry-type">{entry.type}</span>
                <span className="entry-target">{entry.target}</span>
                <span className={`severity-badge ${getSeverityClass(entry.severity)}`}>
                  {entry.severity}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
