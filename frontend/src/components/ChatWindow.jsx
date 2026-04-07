import { useEffect, useRef } from 'react'
import Message from './Message'

function ChatWindow({ messages, loading, topic }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="chat-window">
      {messages.length === 0 && (
        <p className="chat-empty">
          {topic
            ? `Ask me anything about ${topic.replace(/_/g, ' ')}.`
            : 'Select a topic above or ask me anything about nutrition.'}
        </p>
      )}
      {messages.map((msg, i) => (
        <Message key={i} role={msg.role} content={msg.content} sources={msg.sources} />
      ))}
      {loading && (
        <p style={{ color: '#999', fontStyle: 'italic' }}>Thinking...</p>
      )}
      <div ref={bottomRef} />
    </div>
  )
}

export default ChatWindow
