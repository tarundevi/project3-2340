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
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [statsRes, logsRes] = await Promise.all([
        fetch('/api/admin/stats'),
        fetch('/api/admin/logs?limit=50'),
      ])
      setStats(await statsRes.json())
      setLogs(await logsRes.json())
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

  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <h2>Usage Logs</h2>
        <button className="refresh-btn" onClick={fetchData} disabled={loading}>
          {loading ? 'Loading…' : 'Refresh'}
        </button>
      </div>

      {error && <p className="admin-error">{error}</p>}

      {stats && (
        <div className="stats-row">
          <StatCard label="Total Queries" value={stats.total_queries} />
          <StatCard label="Successful" value={stats.successful_queries} />
          <StatCard label="Avg Response (ms)" value={stats.avg_response_time_ms} />
          <StatCard label="Min (ms)" value={stats.min_response_time_ms} />
          <StatCard label="Max (ms)" value={stats.max_response_time_ms} />
        </div>
      )}

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
