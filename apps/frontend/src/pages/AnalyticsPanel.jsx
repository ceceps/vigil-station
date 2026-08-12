import { useState, useEffect } from 'react'
import api from '../api/client'
import Shimmer from '../components/Shimmer'

function AnalyticsPanel() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadAnalytics()
  }, [])

  const loadAnalytics = async () => {
    try {
      setLoading(true)
      const result = await api.getAnalyticsInsights()
      setData(result)
      setError(null)
    } catch (err) {
      console.error('Failed to load analytics:', err)
      setError('Failed to load operational analytics data')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="analytics-panel">
      <div className="section-header">
        <h2>📊 Historical AI Analytics & Reasoning Insights</h2>
        <button onClick={loadAnalytics} className="refresh-button">
          🔄 Refresh
        </button>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {loading ? (
        <>
          <Shimmer type="stats" />
          <Shimmer type="card" rows={3} />
        </>
      ) : data ? (
        <>
          <div className="stats">
            <div className="stat-card">
              <div className="stat-value">{data.summary.total_conflicts}</div>
              <div className="stat-label">Logged Conflicts</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{data.summary.total_recommendations}</div>
              <div className="stat-label">AI Recommendations</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{data.summary.approval_rate_percent}%</div>
              <div className="stat-label">AI Approval Rate</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{data.summary.busiest_ground_station}</div>
              <div className="stat-label">Top Conflict Station</div>
            </div>
          </div>

          <div className="analytics-card" style={{ background: 'var(--card-bg)', padding: '1.5rem', borderRadius: '10px', marginBottom: '1.5rem', border: '1px solid var(--border-color)' }}>
            <h3>🤖 Executive Operational Synthesis</h3>
            <p className="reasoning-text" style={{ fontSize: '1.05rem', lineHeight: '1.6', color: 'var(--text-color)' }}>
              {data.insights_reasoning}
            </p>
          </div>

          {data.recent_overrides && data.recent_overrides.length > 0 && (
            <div className="analytics-card" style={{ background: 'var(--card-bg)', padding: '1.5rem', borderRadius: '10px', marginBottom: '1.5rem', border: '1px solid var(--border-color)' }}>
              <h3>📝 Recent Operator Override Reasons</h3>
              <ul style={{ paddingLeft: '1.2rem', marginTop: '0.5rem' }}>
                {data.recent_overrides.map((reason, idx) => (
                  <li key={idx} style={{ marginBottom: '0.5rem', color: 'var(--text-color)' }}>
                    "{reason}"
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="analytics-card" style={{ background: 'var(--card-bg)', padding: '1.5rem', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            <h3>📜 Historical Database Audit Log</h3>
            <p style={{ color: 'var(--subtitle-color)', fontSize: '0.9rem' }}>
              Recorded conflicts in database: <strong>{data.conflicts_history ? data.conflicts_history.length : 0}</strong> | 
              Recorded AI recommendations: <strong>{data.recommendations_history ? data.recommendations_history.length : 0}</strong>
            </p>
          </div>
        </>
      ) : null}
    </div>
  )
}

export default AnalyticsPanel
