import { useEffect, useState } from 'react'

const TOPICS = [
  { value: '', label: 'All Topics' },
  { value: 'macronutrients', label: 'Macronutrients' },
  { value: 'vitamins_minerals', label: 'Vitamins & Minerals' },
  { value: 'diet_plans', label: 'Diet Plans' },
  { value: 'weight_management', label: 'Weight Management' },
  { value: 'sports_nutrition', label: 'Sports Nutrition' },
  { value: 'hydration', label: 'Hydration' },
  { value: 'digestive_health', label: 'Digestive Health' },
  { value: 'food_safety', label: 'Food Safety' },
]

const INITIAL_TEXT_FORM = {
  title: '',
  url: '',
  topic: '',
  content: '',
}

const INITIAL_URL_FORM = {
  url: '',
  topic: '',
}

const INITIAL_FILE_FORM = {
  topic: '',
  file: null,
}

function TopicField({ value, onChange, id }) {
  return (
    <select id={id} className="developer-select" value={value} onChange={(e) => onChange(e.target.value)}>
      {TOPICS.map((topic) => (
        <option key={topic.value} value={topic.value}>
          {topic.label}
        </option>
      ))}
    </select>
  )
}

export default function DeveloperDashboard() {
  const [mode, setMode] = useState('text')
  const [textForm, setTextForm] = useState(INITIAL_TEXT_FORM)
  const [urlForm, setUrlForm] = useState(INITIAL_URL_FORM)
  const [fileForm, setFileForm] = useState(INITIAL_FILE_FORM)
  const [collection, setCollection] = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [deleting, setDeleting] = useState(null)
  const [maintenanceAction, setMaintenanceAction] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadCollection = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/developer/collection')
      const data = await response.json()
      setCollection(data)
    } catch {
      setError('Failed to load developer data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCollection()
  }, [])

  const handleDelete = async (document) => {
    if (!window.confirm(`Remove "${document.title}" from the knowledge base?`)) return

    const key = `${document.title}::${document.url}::${document.topic}`
    setDeleting(key)
    setError('')
    setSuccess('')

    try {
      const response = await fetch('/api/developer/document', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: document.title,
          url: document.url,
          topic: document.topic,
        }),
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Delete failed.')
      }

      setSuccess(data.message)
      setCollection(data.collection)
    } catch (err) {
      setError(err.message)
    } finally {
      setDeleting(null)
    }
  }

  const handleMaintenance = async (action) => {
    const labels = {
      clear: 'clear the knowledge base',
      reload: 'reload embeddings while keeping the current documents',
    }

    if (!window.confirm(`Are you sure you want to ${labels[action]}?`)) {
      return
    }

    setMaintenanceAction(action)
    setError('')
    setSuccess('')

    try {
      const response = await fetch(`/api/developer/collection/${action}`, {
        method: 'POST',
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || `Failed to ${action} knowledge base.`)
      }

      setSuccess(data.message)
      setCollection(data.collection)
    } catch (err) {
      setError(err.message)
    } finally {
      setMaintenanceAction('')
    }
  }

  const handleTextSubmit = async (event) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setSuccess('')

    try {
      const response = await fetch('/api/developer/ingest/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(textForm),
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Text ingestion failed.')
      }

      setSuccess(data.message)
      setCollection(data.collection)
      setTextForm(INITIAL_TEXT_FORM)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleUrlSubmit = async (event) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setSuccess('')

    try {
      const response = await fetch('/api/developer/ingest/url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(urlForm),
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'URL ingestion failed.')
      }

      setSuccess(data.message)
      setCollection(data.collection)
      setUrlForm(INITIAL_URL_FORM)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleFileSubmit = async (event) => {
    event.preventDefault()
    if (!fileForm.file) {
      setError('Choose a file to upload.')
      return
    }

    setSubmitting(true)
    setError('')
    setSuccess('')

    try {
      const formData = new FormData()
      formData.append('file', fileForm.file)
      formData.append('topic', fileForm.topic)

      const response = await fetch('/api/developer/ingest/file', {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'File upload failed.')
      }

      setSuccess(data.message)
      setCollection(data.collection)
      setFileForm(INITIAL_FILE_FORM)
      event.target.reset()
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="developer-dashboard">
      <div className="admin-header">
        <h2>Knowledge Base</h2>
        <button className="refresh-btn" onClick={loadCollection} disabled={loading || submitting}>
          {loading ? 'Loading…' : 'Refresh'}
        </button>
      </div>

      <div className="stats-row">
        <div className="stat-card">
          <span className="stat-value">{collection?.chunk_count ?? 0}</span>
          <span className="stat-label">Stored Chunks</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{collection?.documents?.length ?? 0}</span>
          <span className="stat-label">Visible Sources</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{collection?.exists ? 'Ready' : 'Empty'}</span>
          <span className="stat-label">Collection State</span>
        </div>
      </div>

      <div className="developer-panel">
        <div className="developer-header">
          <h3>Maintenance</h3>
        </div>

        <p className="developer-help">
          Clear removes all documents and embeddings. Reload keeps the current documents but rebuilds their embeddings in a fresh Chroma collection.
        </p>

        <div className="maintenance-info-card">
          <strong>Clear vs Reload</strong>
          <p>Clear: deletes every stored document and embedding.</p>
          <p>Reload: keeps documents, clears the old embeddings, and regenerates embeddings from those documents.</p>
        </div>

        <div className="maintenance-actions">
          <button
            className="refresh-btn danger-btn"
            onClick={() => handleMaintenance('clear')}
            disabled={loading || submitting || Boolean(maintenanceAction)}
            type="button"
          >
            {maintenanceAction === 'clear' ? 'Clearing…' : 'Clear Knowledge Base'}
          </button>
          <button
            className="refresh-btn"
            onClick={() => handleMaintenance('reload')}
            disabled={loading || submitting || Boolean(maintenanceAction)}
            type="button"
          >
            {maintenanceAction === 'reload' ? 'Reloading…' : 'Reload Clean Collection'}
          </button>
        </div>
      </div>

      <div className="developer-panel">
        <div className="developer-header">
          <h3>Ingest Data</h3>
          <div className="nav-tabs">
            <button
              className={`nav-tab${mode === 'text' ? ' active' : ''}`}
              onClick={() => setMode('text')}
              type="button"
            >
              Paste Text
            </button>
            <button
              className={`nav-tab${mode === 'url' ? ' active' : ''}`}
              onClick={() => setMode('url')}
              type="button"
            >
              Import URL
            </button>
            <button
              className={`nav-tab${mode === 'file' ? ' active' : ''}`}
              onClick={() => setMode('file')}
              type="button"
            >
              Upload File
            </button>
          </div>
        </div>

        <p className="developer-help">
          Use one of three ingestion methods to add sources to Chroma without leaving the app.
        </p>

        {error && <p className="admin-error">{error}</p>}
        {success && <p className="developer-success">{success}</p>}

        {mode === 'text' ? (
          <form className="developer-form" onSubmit={handleTextSubmit}>
            <label className="developer-field">
              <span>Title</span>
              <input
                className="developer-input"
                type="text"
                value={textForm.title}
                onChange={(e) => setTextForm((prev) => ({ ...prev, title: e.target.value }))}
                placeholder="USDA Protein Basics"
                required
              />
            </label>

            <label className="developer-field">
              <span>Source URL</span>
              <input
                className="developer-input"
                type="url"
                value={textForm.url}
                onChange={(e) => setTextForm((prev) => ({ ...prev, url: e.target.value }))}
                placeholder="https://example.com/article"
              />
            </label>

            <label className="developer-field">
              <span>Topic</span>
              <TopicField
                id="text-topic"
                value={textForm.topic}
                onChange={(value) => setTextForm((prev) => ({ ...prev, topic: value }))}
              />
            </label>

            <label className="developer-field">
              <span>Document Text</span>
              <textarea
                className="developer-textarea"
                value={textForm.content}
                onChange={(e) => setTextForm((prev) => ({ ...prev, content: e.target.value }))}
                placeholder="Paste article text, notes, or structured nutrition guidance here."
                rows={10}
                required
              />
            </label>

            <button className="developer-submit" type="submit" disabled={submitting}>
              {submitting ? 'Saving…' : 'Add Text Source'}
            </button>
          </form>
        ) : mode === 'url' ? (
          <form className="developer-form" onSubmit={handleUrlSubmit}>
            <label className="developer-field">
              <span>Page URL</span>
              <input
                className="developer-input"
                type="url"
                value={urlForm.url}
                onChange={(e) => setUrlForm((prev) => ({ ...prev, url: e.target.value }))}
                placeholder="https://example.com/article"
                required
              />
            </label>

            <label className="developer-field">
              <span>Topic</span>
              <TopicField
                id="url-topic"
                value={urlForm.topic}
                onChange={(value) => setUrlForm((prev) => ({ ...prev, topic: value }))}
              />
            </label>

            <button className="developer-submit" type="submit" disabled={submitting}>
              {submitting ? 'Importing…' : 'Import From URL'}
            </button>
          </form>
        ) : (
          <form className="developer-form" onSubmit={handleFileSubmit}>
            <label className="developer-field">
              <span>File</span>
              <input
                className="developer-input"
                type="file"
                accept=".txt,.md,.markdown,.json,.csv,.pdf"
                onChange={(e) => setFileForm((prev) => ({ ...prev, file: e.target.files?.[0] ?? null }))}
                required
              />
            </label>

            <label className="developer-field">
              <span>Topic</span>
              <TopicField
                id="file-topic"
                value={fileForm.topic}
                onChange={(value) => setFileForm((prev) => ({ ...prev, topic: value }))}
              />
            </label>

            <p className="developer-help">
              Supported file types: `.txt`, `.md`, `.markdown`, `.json`, `.csv`, `.pdf`
            </p>

            <button className="developer-submit" type="submit" disabled={submitting}>
              {submitting ? 'Uploading…' : 'Upload File'}
            </button>
          </form>
        )}
      </div>

      <div className="logs-table-wrapper">
        <table className="logs-table">
          <thead>
            <tr>
              <th>Source</th>
              <th>Topic</th>
              <th>Link</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {collection?.documents?.length === 0 && !loading && (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '16px' }}>
                  No sources yet.
                </td>
              </tr>
            )}
            {collection?.documents?.map((document, index) => {
              const key = `${document.title}::${document.url}::${document.topic}`
              return (
                <tr key={`${document.title}-${index}`}>
                  <td>{document.title}</td>
                  <td>{document.topic || '—'}</td>
                  <td>
                    {document.url ? (
                      <a className="table-link" href={document.url} target="_blank" rel="noreferrer">
                        Open
                      </a>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td>
                    <button
                      className="delete-btn"
                      onClick={() => handleDelete(document)}
                      disabled={deleting === key || submitting}
                    >
                      {deleting === key ? 'Removing…' : 'Delete'}
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
