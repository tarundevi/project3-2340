import { useState } from 'react'
import ChatWindow from './components/ChatWindow'
import MessageInput from './components/MessageInput'
import TopicSelector from './components/TopicSelector'
import AdminDashboard from './components/AdminDashboard'
import DeveloperDashboard from './components/DeveloperDashboard'
import { apiUrl } from './lib/api'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [topic, setTopic] = useState('')
  const [view, setView] = useState('chat')

  const handleTopicChange = (newTopic) => {
    setTopic(newTopic)
    setMessages([])
  }

  const sendMessage = async (text) => {
    const userMessage = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)

    try {
      const res = await fetch(apiUrl('/api/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, topic }),
      })
      const data = await res.json()
      const botMessage = {
        role: 'bot',
        content: data.response,
        sources: Array.isArray(data.sources) ? data.sources : [],
      }
      setMessages((prev) => [...prev, botMessage])
    } catch {
      const errorMessage = {
        role: 'bot',
        content: 'Sorry, something went wrong.',
        sources: [],
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
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
