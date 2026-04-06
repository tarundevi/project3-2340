import { useState } from 'react'
import ChatWindow from './components/ChatWindow'
import MessageInput from './components/MessageInput'
import TopicSelector from './components/TopicSelector'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [topic, setTopic] = useState('')

  const handleTopicChange = (newTopic) => {
    setTopic(newTopic)
    setMessages([])
  }

  const sendMessage = async (text) => {
    const userMessage = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, topic }),
      })
      const data = await res.json()
      const botMessage = { role: 'bot', content: data.response }
      setMessages((prev) => [...prev, botMessage])
    } catch {
      const errorMessage = { role: 'bot', content: 'Sorry, something went wrong.' }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <h1>NutriBot</h1>
      <TopicSelector value={topic} onChange={handleTopicChange} />
      <ChatWindow messages={messages} loading={loading} topic={topic} />
      <MessageInput onSend={sendMessage} disabled={loading} topic={topic} />
    </div>
  )
}

export default App
