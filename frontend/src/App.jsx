import { useEffect, useState } from 'react'
import ChatWindow from './components/ChatWindow'
import MessageInput from './components/MessageInput'
import TopicSelector from './components/TopicSelector'
import AdminDashboard from './components/AdminDashboard'
import DeveloperDashboard from './components/DeveloperDashboard'
import AuthPanel from './components/AuthPanel'
import { apiRequest } from './lib/api'
import './App.css'

const TOKEN_STORAGE_KEY = 'nutribot.auth.token'

function App() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [topic, setTopic] = useState('')
  const [view, setView] = useState('chat')
  const [token, setToken] = useState('')
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [authSubmitting, setAuthSubmitting] = useState(false)
  const [authError, setAuthError] = useState('')

  useEffect(() => {
    const restoreSession = async () => {
      const storedToken = window.localStorage.getItem(TOKEN_STORAGE_KEY)
      if (!storedToken) {
        setAuthLoading(false)
        return
      }

      try {
        const me = await apiRequest('/api/auth/me', {}, storedToken)
        setToken(storedToken)
        setUser(me)
      } catch {
        window.localStorage.removeItem(TOKEN_STORAGE_KEY)
      } finally {
        setAuthLoading(false)
      }
    }

    restoreSession()
  }, [])

  const handleTopicChange = (newTopic) => {
    setTopic(newTopic)
    setMessages([])
  }

  const handleAuth = async ({ mode, email, password }) => {
    setAuthSubmitting(true)
    setAuthError('')

    try {
      const data = await apiRequest(`/api/auth/${mode}`, {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      setToken(data.access_token)
      setUser(data.user)
      window.localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token)
    } catch (error) {
      setAuthError(error.message)
    } finally {
      setAuthSubmitting(false)
    }
  }

  const handleLogout = () => {
    setToken('')
    setUser(null)
    setMessages([])
    setTopic('')
    setView('chat')
    window.localStorage.removeItem(TOKEN_STORAGE_KEY)
  }

  const sendMessage = async (text) => {
    const userMessage = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)

    try {
      const data = await apiRequest('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ message: text, topic }),
      }, token)
      const botMessage = {
        role: 'bot',
        content: data.response,
        sources: Array.isArray(data.sources) ? data.sources : [],
      }
      setMessages((prev) => [...prev, botMessage])
    } catch (error) {
      const errorMessage = {
        role: 'bot',
        content: error.message || 'Sorry, something went wrong.',
        sources: [],
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  if (authLoading) {
    return <div className="app auth-loading">Restoring session…</div>
  }

  if (!user) {
    return (
      <div className="app">
        <AuthPanel onSubmit={handleAuth} loading={authSubmitting} error={authError} />
      </div>
    )
  }

  return (
    <div className="app">
      <div className="app-nav">
        <div className="app-logo">
          <div className="app-logo-mark">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C8 2 5 5 5 9c0 2.4 1.1 4.5 2.8 5.9L7 20h10l-.8-5.1C17.9 13.5 19 11.4 19 9c0-4-3-7-7-7z"/>
            </svg>
          </div>
          NutriBot
        </div>
        <div className="app-nav-right">
          <div className="nav-tabs">
            <button
              className={`nav-tab${view === 'chat' ? ' active' : ''}`}
              onClick={() => setView('chat')}
            >
              Chat
            </button>
            <button
              className={`nav-tab${view === 'admin' ? ' active' : ''}`}
              onClick={() => setView('admin')}
            >
              Admin
            </button>
            <button
              className={`nav-tab${view === 'developer' ? ' active' : ''}`}
              onClick={() => setView('developer')}
            >
              Developer
            </button>
          </div>
          <div className="session-chip">
            <span>{user.email}</span>
            <button type="button" className="session-logout" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </div>
      </div>

      {view === 'chat' ? (
        <>
          <TopicSelector value={topic} onChange={handleTopicChange} />
          <ChatWindow messages={messages} loading={loading} topic={topic} />
          <MessageInput onSend={sendMessage} disabled={loading} topic={topic} />
        </>
      ) : view === 'admin' ? (
        <AdminDashboard />
      ) : (
        <DeveloperDashboard />
      )}
    </div>
  )
}

export default App
