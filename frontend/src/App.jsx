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
        <h1>NutriBot</h1>
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
