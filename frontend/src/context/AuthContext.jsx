import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)
const TOKEN_KEY = 'facilityops-token'
import { API_BASE_URL } from '../services/apiConfig'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))
  const [username, setUsername] = useState(null)
  const [retryCount, setRetryCount] = useState(0)
  const retry = useCallback(() => setRetryCount(n => n + 1), [])
  // 'checking' while we verify a stored token is still valid (not expired,
  // user still exists) — prevents a flash of the login page for someone
  // who's already logged in, and equally prevents briefly showing the
  // dashboard for a token that's actually stale before redirecting away.
  const [status, setStatus] = useState(token ? 'checking' : 'anonymous')

  useEffect(() => {
    if (!token) {
      setStatus('anonymous')
      return
    }
    let cancelled = false
    const controller = new AbortController()
    setStatus('checking')
    axios.get(`${API_BASE_URL}/auth/me`, { headers: { Authorization: `Bearer ${token}` }, timeout: 90000, signal: controller.signal })
      .then(r => {
        if (cancelled) return
        setUsername(r.data.username)
        setStatus('authenticated')
      })
      .catch((error) => {
        if (cancelled) return
        if (error.response?.status !== 401) {
          setStatus('unavailable')
          return
        }
        localStorage.removeItem(TOKEN_KEY)
        setToken(null)
        setUsername(null)
        setStatus('anonymous')
      })
    return () => { cancelled = true; controller.abort() }
  }, [token, retryCount])

  const login = useCallback(async (username, password) => {
    const r = await axios.post(`${API_BASE_URL}/auth/login`, { username, password }, { timeout: 90000 })
    localStorage.setItem(TOKEN_KEY, r.data.access_token)
    setToken(r.data.access_token)
    setUsername(r.data.username)
    setStatus('authenticated')
  }, [])

  const register = useCallback(async (username, password) => {
    // Backend auto-logs-in on successful signup (returns the same shape
    // as /auth/login) — store the token immediately so a brand-new user
    // lands straight in the app instead of hitting the login form a
    // second time right after signing up.
    const r = await axios.post(`${API_BASE_URL}/auth/register`, { username, password }, { timeout: 90000 })
    localStorage.setItem(TOKEN_KEY, r.data.access_token)
    setToken(r.data.access_token)
    setUsername(r.data.username)
    setStatus('authenticated')
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUsername(null)
    setStatus('anonymous')
  }, [])

  return (
    <AuthContext.Provider value={{ token, username, status, login, register, logout, retry }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
