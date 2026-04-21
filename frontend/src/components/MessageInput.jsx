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
    <form onSubmit={handleSubmit} className="message-input-form">
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={topic ? `Ask about ${topic.replace(/_/g, ' ')}…` : 'Ask about nutrition…'}
        disabled={disabled}
        className="message-input"
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="send-btn"
      >
        Send
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M1 6h10M6 1l5 5-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>
    </form>
  )
}

export default MessageInput
