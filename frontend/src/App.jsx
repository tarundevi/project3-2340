import { useEffect, useState } from 'react'
import ChatWindow from './components/ChatWindow'
import MessageInput from './components/MessageInput'
import TopicSelector from './components/TopicSelector'
import AdminDashboard from './components/AdminDashboard'
import DeveloperDashboard from './components/DeveloperDashboard'
import AuthPanel from './components/AuthPanel'
import ConversationSidebar from './components/ConversationSidebar'
import ProfilePanel from './components/ProfilePanel'
import IngredientChecker from './components/IngredientChecker'
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
  const [conversations, setConversations] = useState([])
  const [activeConversationId, setActiveConversationId] = useState('')
  const [conversationLoading, setConversationLoading] = useState(false)
  const [profile, setProfile] = useState({ raw_text: '', summary: [], updated_at: '' })
  const [profileLoading, setProfileLoading] = useState(false)
  const [profileSaving, setProfileSaving] = useState(false)
  const role = user?.role || 'user'
  const canViewAdmin = role === 'admin'
  const canViewDeveloper = role === 'admin' || role === 'developer'

  const loadConversation = async (conversationId, authToken = token) => {
    if (!conversationId) {
      setMessages([])
      setActiveConversationId('')
      return
    }

    setConversationLoading(true)
    try {
      const data = await apiRequest(`/api/conversations/${conversationId}`, {}, authToken)
      setActiveConversationId(conversationId)
      setMessages(data.messages || [])
      setTopic(data.conversation?.topic || '')
    } finally {
      setConversationLoading(false)
    }
  }

  const loadConversations = async (authToken = token) => {
    const data = await apiRequest('/api/conversations', {}, authToken)
    setConversations(Array.isArray(data) ? data : [])
    return Array.isArray(data) ? data : []
  }

  const loadProfile = async (authToken = token) => {
    setProfileLoading(true)
    try {
      const data = await apiRequest('/api/profile', {}, authToken)
      setProfile(data || { raw_text: '', summary: [], updated_at: '' })
      return data
    } finally {
      setProfileLoading(false)
    }
  }

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
        await loadProfile(storedToken)
        const existingConversations = await loadConversations(storedToken)
        if (existingConversations[0]?.id) {
          await loadConversation(existingConversations[0].id, storedToken)
        }
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
  }

  const handleAuth = async ({ mode, email, password, roleKey }) => {
    setAuthSubmitting(true)
    setAuthError('')

    try {
      const data = await apiRequest(`/api/auth/${mode}`, {
        method: 'POST',
        body: JSON.stringify({ email, password, role_key: roleKey }),
      })
      setToken(data.access_token)
      setUser(data.user)
      window.localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token)
      await loadProfile(data.access_token)
      const existingConversations = await loadConversations(data.access_token)
      if (existingConversations[0]?.id) {
        await loadConversation(existingConversations[0].id, data.access_token)
      } else {
        setMessages([])
        setActiveConversationId('')
      }
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
    setConversations([])
    setActiveConversationId('')
    setProfile({ raw_text: '', summary: [], updated_at: '' })
    window.localStorage.removeItem(TOKEN_STORAGE_KEY)
  }

  useEffect(() => {
    if (view === 'admin' && !canViewAdmin) {
      setView('chat')
    }
    if (view === 'developer' && !canViewDeveloper) {
      setView('chat')
    }
  }, [view, canViewAdmin, canViewDeveloper])

  const createConversation = async () => {
    const conversation = await apiRequest('/api/conversations', {
      method: 'POST',
      body: JSON.stringify({ title: '', topic }),
    }, token)

    const refreshed = await loadConversations(token)
    setActiveConversationId(conversation.id)
    setMessages([])
    if (!refreshed.some((item) => item.id === conversation.id)) {
      setConversations((prev) => [conversation, ...prev])
    }
  }

  const sendMessage = async (text) => {
    const userMessage = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)

    try {
      const data = await apiRequest('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ message: text, topic, conversation_id: activeConversationId }),
      }, token)
      const conversationId = data.conversation_id || activeConversationId
      await loadConversation(conversationId, token)
      await loadConversations(token)
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

  const saveProfile = async (rawText) => {
    setProfileSaving(true)
    try {
      const data = await apiRequest('/api/profile', {
        method: 'PUT',
        body: JSON.stringify({ raw_text: rawText }),
      }, token)
      setProfile(data)
    } finally {
      setProfileSaving(false)
    }
  }

  const checkIngredient = async (ingredient) => {
    return await apiRequest('/api/profile/ingredient-check', {
      method: 'POST',
      body: JSON.stringify({ ingredient }),
    }, token)
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
            {canViewAdmin ? (
              <button
                className={`nav-tab${view === 'admin' ? ' active' : ''}`}
                onClick={() => setView('admin')}
              >
                Admin
              </button>
            ) : null}
            {canViewDeveloper ? (
              <button
                className={`nav-tab${view === 'developer' ? ' active' : ''}`}
                onClick={() => setView('developer')}
              >
                Developer
              </button>
            ) : null}
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
        <div className="chat-layout">
          <ConversationSidebar
            conversations={conversations}
            activeConversationId={activeConversationId}
            loading={conversationLoading}
            onSelect={loadConversation}
            onCreate={createConversation}
          />
          <div className="chat-main">
            <ProfilePanel
              profile={profile}
              loading={profileLoading}
              saving={profileSaving}
              onSave={saveProfile}
            />
            <IngredientChecker onCheck={checkIngredient} hasProfile={Boolean(profile?.raw_text?.trim())} />
            <TopicSelector value={topic} onChange={handleTopicChange} />
            <ChatWindow messages={messages} loading={loading || conversationLoading} topic={topic} />
            <MessageInput onSend={sendMessage} disabled={loading || conversationLoading} topic={topic} />
          </div>
        </div>
      ) : view === 'admin' ? (
        <AdminDashboard token={token} />
      ) : (
        <DeveloperDashboard token={token} />
      )}
    </div>
  )
}

export default App
