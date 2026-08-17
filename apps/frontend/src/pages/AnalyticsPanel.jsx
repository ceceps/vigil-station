import { useState, useEffect } from 'react'
import api from '../api/client'
import Shimmer from '../components/Shimmer'

function AnalyticsPanel() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')
  const [activePreset, setActivePreset] = useState('all')

  useEffect(() => {
    loadAnalytics('', '', 'all')
  }, [])

  const handlePresetChange = (presetKey) => {
    setActivePreset(presetKey)
    const now = new Date()
    let start = ''
    let end = now.toISOString().split('T')[0]

    if (presetKey === 'today') {
      start = now.toISOString().split('T')[0]
      end = now.toISOString().split('T')[0]
    } else if (presetKey === '7d') {
      const d = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      start = d.toISOString().split('T')[0]
    } else if (presetKey === '30d') {
      const d = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      start = d.toISOString().split('T')[0]
    } else if (presetKey === 'all') {
      start = data?.data_start_date || ''
      end = data?.data_end_date || ''
    }

    setStartTime(start)
    setEndTime(end)
    loadAnalytics(start, end, presetKey)
  }

  const loadAnalytics = async (customStart = startTime, customEnd = endTime, presetKey = activePreset) => {
    try {
      setLoading(true)
      const params = {}
      if (customStart) params.start = customStart
      if (customEnd) params.end = customEnd

      const result = await api.getAnalyticsInsights(params)
      setData(result)
      setError(null)

      // Auto-set the date inputs from the data span (e.g. 202 logged conflicts) if all-time or empty
      if (result.data_start_date && result.data_end_date) {
        if (presetKey === 'all' || (!customStart && !customEnd)) {
          setStartTime(result.data_start_date)
          setEndTime(result.data_end_date)
        }
      }
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
        <h2>📊 Operational Analytics & AI Analyst Synthesis</h2>
        <button onClick={() => loadAnalytics()} className="refresh-button">
          🔄 Refresh
        </button>
      </div>

      <div className="filters" style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <div className="filter-group">
          <label>Timeframe Preset:</label>
          <div style={{ display: 'flex', gap: '0.4rem' }}>
            <button
              type="button"
              className={`refresh-button ${activePreset === 'all' ? 'active' : ''}`}
              style={{ opacity: activePreset === 'all' ? 1 : 0.7 }}
              onClick={() => handlePresetChange('all')}
            >
              All Time
            </button>
            <button
              type="button"
              className={`refresh-button ${activePreset === 'today' ? 'active' : ''}`}
              style={{ opacity: activePreset === 'today' ? 1 : 0.7 }}
              onClick={() => handlePresetChange('today')}
            >
              Today
            </button>
            <button
              type="button"
              className={`refresh-button ${activePreset === '7d' ? 'active' : ''}`}
              style={{ opacity: activePreset === '7d' ? 1 : 0.7 }}
              onClick={() => handlePresetChange('7d')}
            >
              Last 7 Days
            </button>
            <button
              type="button"
              className={`refresh-button ${activePreset === '30d' ? 'active' : ''}`}
              style={{ opacity: activePreset === '30d' ? 1 : 0.7 }}
              onClick={() => handlePresetChange('30d')}
            >
              Last 30 Days
            </button>
          </div>
        </div>

        <div className="filter-group">
          <label>Start Date:</label>
          <input
            type="date"
            value={startTime}
            onChange={(e) => {
              setStartTime(e.target.value)
              setActivePreset('custom')
            }}
          />
        </div>

        <div className="filter-group">
          <label>End Date:</label>
          <input
            type="date"
            value={endTime}
            min={startTime}
            onChange={(e) => {
              setEndTime(e.target.value)
              setActivePreset('custom')
            }}
          />
        </div>

        <button
          type="button"
          className="refresh-button"
          onClick={() => loadAnalytics(startTime, endTime, 'custom')}
          style={{ marginTop: '1.2rem', padding: '0.5rem 1rem' }}
        >
          🔍 Apply Filter
        </button>
      </div>

      {data?.data_start_date && data?.data_end_date && (
        <div style={{ fontSize: '0.85rem', color: 'var(--subtitle-color)', marginTop: '-0.8rem', marginBottom: '1.2rem' }}>
          📅 <strong>Dataset Scope:</strong> {data.data_start_date} to {data.data_end_date} ({data.summary.total_conflicts} conflicts recorded in database)
        </div>
      )}

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
              <div className="stat-label">Top Contention Station</div>
            </div>
          </div>

          <div className="analytics-card" style={{ background: 'var(--card-bg)', padding: '1.5rem', borderRadius: '10px', marginBottom: '1.5rem', border: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.8rem' }}>
              <h3>🤖 AI Analyst Operational Report ({data.timeframe_label || 'Selected Period'})</h3>
              <button
                className="refresh-button"
                style={{ fontSize: '0.85rem' }}
                onClick={() => loadAnalytics(startTime, endTime)}
              >
                ✨ Re-Analyze Range
              </button>
            </div>
            <div
              className="reasoning-text"
              style={{
                fontSize: '1.05rem',
                lineHeight: '1.7',
                color: 'var(--text-color)',
                whiteSpace: 'pre-line'
              }}
            >
              {data.insights_reasoning}
            </div>
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
              Timeframe: <strong>{data.timeframe_label}</strong> | 
              Recorded conflicts: <strong>{data.conflicts_history ? data.conflicts_history.length : 0}</strong> | 
              Recorded AI recommendations: <strong>{data.recommendations_history ? data.recommendations_history.length : 0}</strong> | 
              Recorded operator decisions: <strong>{data.schedules_history ? data.schedules_history.length : 0}</strong>
            </p>
          </div>
        </>
      ) : null}
    </div>
  )
}

export default AnalyticsPanel
