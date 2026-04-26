import { useEffect, useState } from 'react'
import { apiRequest } from '../lib/api'

const LATENCY_THRESHOLD_MS = 5000

function StatCard({ label, value, alert }) {
  return (
    <div className={`stat-card${alert ? ' stat-card-alert' : ''}`}>
      <span className="stat-value">{value ?? '—'}</span>
      <span className="stat-label">{label}</span>
    </div>
  )
}

function LatencyChart({ buckets }) {
  if (!buckets || buckets.length === 0) {
    return <div className="perf-chart-empty">No data for the last 24 hours</div>
  }

  const BAR_W = 18
  const BAR_GAP = 3
  const PAD_LEFT = 44
  const PAD_BOTTOM = 22
  const PAD_TOP = 14
  const CHART_H = 80

  const maxVal = Math.max(...buckets.map(b => b.avg_latency_ms || 0), LATENCY_THRESHOLD_MS)
  const svgW = PAD_LEFT + buckets.length * (BAR_W + BAR_GAP) + 10
  const svgH = CHART_H + PAD_BOTTOM + PAD_TOP

  const toY = (v) => PAD_TOP + CHART_H - (v / maxVal) * CHART_H
  const thresholdY = toY(LATENCY_THRESHOLD_MS)

  const barColor = (ms) => {
    if (!ms) return '#e0e0e0'
    if (ms > LATENCY_THRESHOLD_MS) return '#c0392b'
    if (ms > LATENCY_THRESHOLD_MS * 0.7) return '#e67e22'
    return '#1a5c38'
  }

  const hourLabel = (iso) => {
    const h = iso.slice(11, 13)
    return `${h}h`
  }

  return (
    <div className="perf-chart-wrapper">
      <svg
        viewBox={`0 0 ${svgW} ${svgH}`}
        style={{ width: '100%', height: svgH, display: 'block' }}
        aria-label="Hourly avg latency for the last 24 hours"
      >
        {/* Y-axis */}
        <line
          x1={PAD_LEFT} y1={PAD_TOP}
          x2={PAD_LEFT} y2={PAD_TOP + CHART_H}
          stroke="#e0e0e0" strokeWidth="1"
        />
        <text x={PAD_LEFT - 4} y={PAD_TOP + 4} textAnchor="end" fontSize="8" fill="#a8a8a8">
          {maxVal >= 1000 ? `${(maxVal / 1000).toFixed(0)}s` : `${maxVal}ms`}
        </text>
        <text x={PAD_LEFT - 4} y={PAD_TOP + CHART_H} textAnchor="end" fontSize="8" fill="#a8a8a8">0</text>

        {/* Threshold line */}
        <line
          x1={PAD_LEFT} y1={thresholdY}
          x2={svgW - 10} y2={thresholdY}
          stroke="#c0392b" strokeWidth="1" strokeDasharray="4 3" opacity="0.7"
        />
        <text x={PAD_LEFT - 4} y={thresholdY} textAnchor="end" fontSize="8" fill="#c0392b" dy="4">5s</text>

        {/* Bars */}
        {buckets.map((b, i) => {
          const x = PAD_LEFT + i * (BAR_W + BAR_GAP)
          const barH = ((b.avg_latency_ms || 0) / maxVal) * CHART_H
          const y = PAD_TOP + CHART_H - barH
          return (
            <g key={b.hour}>
              <rect x={x} y={y} width={BAR_W} height={barH || 1}
                fill={barColor(b.avg_latency_ms)} opacity="0.85" rx="1" />
              {b.failures > 0 && (
                <circle cx={x + BAR_W / 2} cy={y - 5} r="3" fill="#c0392b" />
              )}
              <text
                x={x + BAR_W / 2} y={PAD_TOP + CHART_H + 12}
                textAnchor="middle" fontSize="7.5" fill="#a8a8a8"
              >
                {hourLabel(b.hour)}
              </text>
            </g>
          )
        })}
      </svg>
      <p className="perf-chart-legend">
        Bars: avg latency / hour &nbsp;·&nbsp; Red dot: failures &nbsp;·&nbsp; Dashed: 5 s target
      </p>
    </div>
  )
}

export default function AdminDashboard({ token }) {
  const [stats, setStats] = useState(null)
  const [perf, setPerf] = useState(null)
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
      const [statsRes, perfRes, logsRes, collectionRes] = await Promise.all([
        apiRequest('/api/admin/stats', {}, token),
        apiRequest('/api/admin/performance', {}, token),
        apiRequest('/api/admin/logs?limit=50', {}, token),
        apiRequest('/api/developer/collection', {}, token),
      ])
      setStats(statsRes)
      setPerf(perfRes)
      setLogs(logsRes)
      setCollection(collectionRes)
    } catch (err) {
      setError(err.message || 'Failed to load admin data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const formatTs = (ts) => new Date(ts).toLocaleString()
  const truncate = (str, n = 60) => str.length > n ? str.slice(0, n) + '…' : str

  const handleMaintenance = async (action) => {
    const labels = {
      clear: 'clear the knowledge base',
      reload: 'reload embeddings while keeping the current documents',
    }
    if (!window.confirm(`Are you sure you want to ${labels[action]}?`)) return

    setMaintenanceAction(action)
    setError(null)
    setSuccess('')
    try {
      const data = await apiRequest(`/api/developer/collection/${action}`, { method: 'POST' }, token)
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
        <h2>Admin Dashboard</h2>
        <button className="refresh-btn" onClick={fetchData} disabled={loading}>
          {loading ? 'Loading…' : 'Refresh'}
        </button>
      </div>

      {error && <p className="admin-error">{error}</p>}
      {success && <p className="developer-success">{success}</p>}

      {/* ── Usage summary ── */}
      {stats && (
        <div className="stats-row">
          <StatCard label="Total Queries" value={stats.total_queries} />
          <StatCard label="Successful" value={stats.successful_queries} />
          <StatCard label="Avg Response (ms)" value={stats.avg_response_time_ms} />
          <StatCard label="Min (ms)" value={stats.min_response_time_ms} />
          <StatCard label="Max (ms)" value={stats.max_response_time_ms} />
        </div>
      )}

      {/* ── Performance Monitor ── */}
      {perf && (
        <div className="developer-panel">
          <div className="developer-header">
            <h3>Performance Monitor</h3>
            <span className="developer-help">Target: p95 &lt; 5 000 ms</span>
          </div>

          <div className="stats-row">
            <StatCard
              label="Failure Rate"
              value={`${perf.failure_rate_pct}%`}
              alert={perf.failure_rate_pct > 5}
            />
            <StatCard
              label="p50 Latency"
              value={perf.p50_ms != null ? `${perf.p50_ms} ms` : '—'}
            />
            <StatCard
              label="p95 Latency"
              value={perf.p95_ms != null ? `${perf.p95_ms} ms` : '—'}
              alert={perf.p95_ms > LATENCY_THRESHOLD_MS}
            />
            <StatCard
              label="p99 Latency"
              value={perf.p99_ms != null ? `${perf.p99_ms} ms` : '—'}
              alert={perf.p99_ms > LATENCY_THRESHOLD_MS}
            />
            <StatCard label="Total Failures" value={perf.total_failures} />
          </div>

          <LatencyChart buckets={perf.hourly_buckets} />

          {perf.recent_failures.length > 0 && (
            <div>
              <p className="developer-help" style={{ marginBottom: '8px' }}>Recent failures</p>
              <div className="logs-table-wrapper">
                <table className="logs-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Timestamp</th>
                      <th>Query</th>
                      <th>Topic</th>
                      <th>Response (ms)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {perf.recent_failures.map((f) => (
                      <tr key={f.id}>
                        <td>{f.id}</td>
                        <td>{formatTs(f.timestamp)}</td>
                        <td title={f.query}>{truncate(f.query)}</td>
                        <td>{f.topic || '—'}</td>
                        <td className="status-err">{f.response_time_ms}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Knowledge Base Maintenance ── */}
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

      {/* ── Query Logs ── */}
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
