import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const API = 'http://localhost:8001'

export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Behavioural biometrics
  const mountTime = useRef(Date.now())
  const keystrokeCount = useRef(0)
  const firstKeystrokeTime = useRef(null)
  const mouseEventCount = useRef(0)

  // Track mouse movement
  useEffect(() => {
    const handler = () => {
      mouseEventCount.current += 1
    }
    window.addEventListener('mousemove', handler)
    return () => window.removeEventListener('mousemove', handler)
  }, [])

  const handleKeystroke = () => {
    if (!firstKeystrokeTime.current) {
      firstKeystrokeTime.current = Date.now()
    }
    keystrokeCount.current += 1
  }

  const computeTypingSpeed = () => {
    if (!firstKeystrokeTime.current || keystrokeCount.current < 2) return 0
    const elapsedMinutes = (Date.now() - firstKeystrokeTime.current) / 60000
    if (elapsedMinutes === 0) return 0
    // chars typed / time in minutes * 12 (rough WPM approximation)
    return (keystrokeCount.current / elapsedMinutes) * (1 / 5) // 5 chars per word
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const timeOnPage = (Date.now() - mountTime.current) / 1000
    const typingSpeed = computeTypingSpeed()

    try {
      const res = await axios.post(`${API}/login`, {
        username,
        password,
        typing_speed_wpm: Math.round(typingSpeed),
        time_on_page_sec: Math.round(timeOnPage),
        mouse_event_count: mouseEventCount.current,
      })

      if (res.data.success) {
        localStorage.setItem('gridshield_token', res.data.token)
        localStorage.setItem('gridshield_behaviour_score', res.data.behaviour_score)
        localStorage.setItem('gridshield_risk_label', res.data.risk_label)
        navigate('/dashboard')
      } else {
        setError(res.data.message || 'ACCESS DENIED')
      }
    } catch (err) {
      setError('CONNECTION FAILED — SERVER OFFLINE')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-logo">
          <h1>GRIDSHIELD //<br />ENGINEER ACCESS PORTAL</h1>
          <div className="logo-subtitle">Secure Authentication Gateway</div>
          <div className="logo-divider" />
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="input-group">
            <label htmlFor="username">Operator ID</label>
            <input
              id="username"
              type="text"
              placeholder="Enter username"
              value={username}
              onChange={(e) => { setUsername(e.target.value); handleKeystroke() }}
              autoComplete="off"
              spellCheck="false"
            />
          </div>

          <div className="input-group">
            <label htmlFor="password">Access Key</label>
            <input
              id="password"
              type="password"
              placeholder="Enter password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); handleKeystroke() }}
              autoComplete="off"
            />
          </div>

          {error && (
            <div className="login-error">
              ⚠ ACCESS DENIED — {error.toUpperCase()}
            </div>
          )}

          <button
            type="submit"
            className="login-btn"
            disabled={loading}
          >
            {loading ? '◌ AUTHENTICATING...' : '▸ AUTHENTICATE'}
          </button>
        </form>
      </div>
    </div>
  )
}
