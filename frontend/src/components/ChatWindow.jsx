import { useEffect, useRef } from 'react'
import Message from './Message'

function ChatWindow({ messages, loading, topic }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  return (
    <div className="chat-window">
      {messages.length === 0 && !loading && (
        <div className="chat-empty">
          <svg className="chat-empty-icon" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="16" cy="16" r="14" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M10 16c0-3.3 2.7-6 6-6s6 2.7 6 6-2.7 6-6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            <circle cx="16" cy="16" r="2" fill="currentColor"/>
          </svg>
          <span>
            {topic
              ? `Ask me anything about ${topic.replace(/_/g, ' ')}.`
              : 'Select a topic above or ask anything about nutrition.'}
          </span>
        </div>
      )}
      {messages.map((msg, i) => (
        <Message key={i} role={msg.role} content={msg.content} sources={msg.sources} />
      ))}
      {loading && (
        <div className="typing-indicator">
          <div className="typing-dot" />
          <div className="typing-dot" />
          <div className="typing-dot" />
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}

export default ChatWindow
