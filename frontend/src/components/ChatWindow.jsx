import { useEffect, useRef } from 'react'
import Message from './Message'

function ChatWindow({ messages, loading, topic }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      border: '1px solid #000',
      padding: '10px',
      marginBottom: '10px',
    }}>
      {messages.length === 0 && (
        <p style={{ color: '#999', textAlign: 'center', marginTop: '20px' }}>
          {topic
            ? `Ask me anything about ${topic.replace(/_/g, ' ')}.`
            : 'Select a topic above or ask me anything about nutrition.'}
        </p>
      )}
      {messages.map((msg, i) => (
        <Message key={i} role={msg.role} content={msg.content} />
      ))}
      {loading && (
        <p style={{ color: '#999', fontStyle: 'italic' }}>Thinking...</p>
      )}
      <div ref={bottomRef} />
    </div>
  )
}

export default ChatWindow
