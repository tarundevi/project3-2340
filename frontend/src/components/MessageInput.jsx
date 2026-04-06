import { useState } from 'react'

function MessageInput({ onSend, disabled, topic }) {
  const [text, setText] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!text.trim()) return
    onSend(text.trim())
    setText('')
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px' }}>
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={topic ? `Ask about ${topic.replace(/_/g, ' ')}...` : 'Ask about nutrition...'}
        disabled={disabled}
        style={{
          flex: 1,
          padding: '8px',
          border: '1px solid #000',
          fontFamily: 'monospace',
          fontSize: '1rem',
        }}
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        style={{
          padding: '8px 16px',
          border: '1px solid #000',
          background: '#000',
          color: '#fff',
          fontFamily: 'monospace',
          fontSize: '1rem',
          cursor: 'pointer',
        }}
      >
        Send
      </button>
    </form>
  )
}

export default MessageInput
