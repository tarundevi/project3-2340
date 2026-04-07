import { useEffect, useState } from 'react'

function StatCard({ label, value }) {
  return (
    <div className="stat-card">
      <span className="stat-value">{value ?? '—'}</span>
      <span className="stat-label">{label}</span>
    </div>
  )
}

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [logs, setLogs] = useState([])
  const [collection, setCollection] = useState(null)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)
  const [maintenanceAction, setMaintenanceAction] = useState('')

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    setSuccess('')
    try {
      const [statsRes, logsRes, collectionRes] = await Promise.all([
        fetch('/api/admin/stats'),
        fetch('/api/admin/logs?limit=50'),
        fetch('/api/developer/collection'),
      ])
      setStats(await statsRes.json())
      setLogs(await logsRes.json())
      setCollection(await collectionRes.json())
    } catch {
      setError('Failed to load admin data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const formatTs = (ts) => {
    const d = new Date(ts)
    return d.toLocaleString()
  }

  const truncate = (str, n = 60) =>
    str.length > n ? str.slice(0, n) + '…' : str

  const handleMaintenance = async (action) => {
    const labels = {
      clear: 'clear the knowledge base',
      reload: 'reload embeddings while keeping the current documents',
    }

    if (!window.confirm(`Are you sure you want to ${labels[action]}?`)) {
      return
    }

    setMaintenanceAction(action)
    setError(null)
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

  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <h2>Usage Logs</h2>
        <button className="refresh-btn" onClick={fetchData} disabled={loading}>
          {loading ? 'Loading…' : 'Refresh'}
        </button>
      </div>

      {error && <p className="admin-error">{error}</p>}
      {success && <p className="developer-success">{success}</p>}

      {stats && (
        <div className="stats-row">
          <StatCard label="Total Queries" value={stats.total_queries} />
          <StatCard label="Successful" value={stats.successful_queries} />
          <StatCard label="Avg Response (ms)" value={stats.avg_response_time_ms} />
          <StatCard label="Min (ms)" value={stats.min_response_time_ms} />
          <StatCard label="Max (ms)" value={stats.max_response_time_ms} />
        </div>
      )}

      <div className="developer-panel">
        <div className="developer-header">
          <h3>Knowledge Base Maintenance</h3>
        </div>

        <div className="stats-row">
          <StatCard label="Stored Chunks" value={collection?.chunk_count ?? 0} />
          <StatCard label="Visible Sources" value={collection?.documents?.length ?? 0} />
          <StatCard label="Collection State" value={collection?.exists ? 'Ready' : 'Empty'} />
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
            disabled={loading || Boolean(maintenanceAction)}
            type="button"
          >
            {maintenanceAction === 'clear' ? 'Clearing…' : 'Clear Knowledge Base'}
          </button>
          <button
            className="refresh-btn"
            onClick={() => handleMaintenance('reload')}
            disabled={loading || Boolean(maintenanceAction)}
            type="button"
          >
            {maintenanceAction === 'reload' ? 'Reloading…' : 'Reload Clean Collection'}
          </button>
        </div>
      </div>

      <div className="logs-table-wrapper">
        <table className="logs-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Timestamp</th>
              <th>Query</th>
              <th>Topic</th>
              <th>Response (ms)</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 && !loading && (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '16px' }}>
                  No logs yet.
                </td>
              </tr>
            )}
            {logs.map((log) => (
              <tr key={log.id}>
                <td>{log.id}</td>
                <td>{formatTs(log.timestamp)}</td>
                <td title={log.query}>{truncate(log.query)}</td>
                <td>{log.topic || '—'}</td>
                <td>{log.response_time_ms}</td>
                <td className={log.success ? 'status-ok' : 'status-err'}>
                  {log.success ? 'OK' : 'Error'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
