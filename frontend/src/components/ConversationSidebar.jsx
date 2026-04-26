export default function ConversationSidebar({
  conversations,
  activeConversationId,
  loading,
  onSelect,
  onCreate,
}) {
  return (
    <aside className="conversation-sidebar">
      <div className="conversation-sidebar-header">
        <div>
          <p className="conversation-kicker">History</p>
          <h2 className="conversation-title">Conversations</h2>
        </div>
        <button type="button" className="refresh-btn" onClick={onCreate} disabled={loading}>
          New Chat
        </button>
      </div>

      <div className="conversation-list">
        {conversations.length === 0 ? (
          <div className="conversation-empty">
            {loading ? 'Loading…' : 'No saved chats yet.'}
          </div>
        ) : (
          conversations.map((conversation) => (
            <button
              key={conversation.id}
              type="button"
              className={`conversation-item${conversation.id === activeConversationId ? ' active' : ''}`}
              onClick={() => onSelect(conversation.id)}
            >
              <span className="conversation-item-title">{conversation.title}</span>
              <span className="conversation-item-preview">
                {conversation.last_message_preview || 'No messages yet.'}
              </span>
            </button>
          ))
        )}
      </div>
    </aside>
  )
}
