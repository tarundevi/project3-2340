function Message({ role, content }) {
  return (
    <div style={{
      padding: '8px 12px',
      margin: '4px 0',
      border: '1px solid #000',
      background: role === 'user' ? '#f0f0f0' : '#fff',
      textAlign: role === 'user' ? 'right' : 'left',
    }}>
      <strong>{role === 'user' ? 'You' : 'NutriBot'}</strong>
      <p style={{ marginTop: '4px' }}>{content}</p>
    </div>
  )
}

export default Message
