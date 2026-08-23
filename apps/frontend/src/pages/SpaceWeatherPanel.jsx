import { useState, useEffect } from 'react'
import api from '../api/client'
import Shimmer from '../components/Shimmer'

function SpaceWeatherPanel() {
  const [spaceWeather, setSpaceWeather] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadSpaceWeather()
  }, [])

  const loadSpaceWeather = async () => {
    try {
      setLoading(true)
      const data = await api.getSpaceWeather()
      setSpaceWeather(data)
      setError(null)
    } catch (err) {
      console.error('Failed to load space weather:', err)
      setError('Failed to load space weather data')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status, dataAvailable) => {
    if (!dataAvailable) return '#ff9800'
    switch (status) {
      case 'extreme': return '#f44336'
      case 'severe': return '#ff5722'
      case 'strong': return '#ff9800'
      case 'disturbed': return '#ffc107'
      case 'unsettled': return '#ffeb3b'
      case 'quiet': return '#4caf50'
      default: return '#9e9e9e'
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'extreme': return '#f44336'
      case 'severe': return '#ff5722'
      case 'strong': return '#ff9800'
      case 'moderate': return '#ffc107'
      case 'minor': return '#4caf50'
      default: return '#9e9e9e'
    }
  }

  const formatTime = (timeStr) => {
    if (!timeStr) return 'N/A'
    try {
      const date = new Date(timeStr)
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'UTC',
        timeZoneName: 'short'
      })
    } catch {
      return timeStr
    }
  }

  const getEventIcon = (eventType) => {
    switch (eventType) {
      case 'solar_flare': return '☀️'
      case 'coronal_mass_ejection': return '💨'
      case 'geomagnetic_storm': return '🧲'
      default: return '🌌'
    }
  }

  if (loading) {
    return (
      <div className="space-weather-panel">
        <div className="section-header">
          <h2>🌞 Space Weather Conditions</h2>
        </div>
        <Shimmer type="stats" />
        <Shimmer type="card" rows={3} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-weather-panel">
        <div className="section-header">
          <h2>🌞 Space Weather Conditions</h2>
          <button onClick={loadSpaceWeather} className="refresh-button">
            🔄 Refresh
          </button>
        </div>
        <div className="error-message">
          ⚠️ {error}
        </div>
      </div>
    )
  }

  const events = spaceWeather?.events || []
  const overallStatus = spaceWeather?.overall_status || 'unknown'
  const communicationImpact = spaceWeather?.communication_impact || {}

  const allEvents = Array.isArray(events) ? events : []

  return (
    <div className="space-weather-panel">
      <div className="section-header">
        <h2>🌞 Space Weather Conditions</h2>
        <button onClick={loadSpaceWeather} className="refresh-button">
          🔄 Refresh
        </button>
      </div>

      <div className="stats">
        <div className="stat-card">
          <div 
            className="stat-value"
            style={{ color: getStatusColor(overallStatus, spaceWeather?.data_available !== false) }}
          >
            {spaceWeather?.data_available === false ? 'UNAVAILABLE' : overallStatus.toUpperCase()}
          </div>
          <div className="stat-label">Overall Status</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{allEvents.length}</div>
          <div className="stat-label">Active Events</div>
        </div>
        <div className="stat-card">
          <div 
            className="stat-value"
            style={{ color: communicationImpact.affected ? '#f44336' : '#4caf50' }}
          >
            {communicationImpact.affected ? 'YES' : 'NO'}
          </div>
          <div className="stat-label">Communication Impact</div>
        </div>
      </div>

      {communicationImpact.affected && (
        <div className="error-message">
          ⚠️ Space weather conditions may affect satellite communication link quality
        </div>
      )}

      {communicationImpact.recommendation && (
        <div className="recommendation-summary">
          <h4>📋 Recommendation</h4>
          <p>{communicationImpact.recommendation}</p>
        </div>
      )}

      {communicationImpact.risk_factors && communicationImpact.risk_factors.length > 0 && (
        <div className="risk-factors">
          <h4>⚠️ Risk Factors</h4>
          <ul>
            {communicationImpact.risk_factors.map((factor, index) => (
              <li key={index}>{factor}</li>
            ))}
          </ul>
        </div>
      )}

      {allEvents.length > 0 ? (
        <div className="events-list">
          <h3>Recent Space Weather Events</h3>
          {allEvents.map((event, index) => (
            <div key={index} className="event-card">
              <div className="event-header">
                <span className="event-icon">{getEventIcon(event.event_type)}</span>
                <span className="event-type">{event.event_type.replace('_', ' ').toUpperCase()}</span>
                <span 
                  className="event-severity"
                  style={{ backgroundColor: getSeverityColor(event.severity) }}
                >
                  {event.severity}
                </span>
              </div>
              <div className="event-details">
                <p><strong>Start:</strong> {formatTime(event.start_time)}</p>
                {event.end_time && (
                  <p><strong>End:</strong> {formatTime(event.end_time)}</p>
                )}
                <p><strong>Description:</strong> {event.description || 'No description available'}</p>
                {event.source_location && (
                  <p><strong>Source:</strong> {event.source_location}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : spaceWeather?.data_available === false ? (
        <div className="error-message" style={{ textAlign: 'center', padding: '20px' }}>
          <div style={{ fontSize: '24px', marginBottom: '10px' }}>⚠️</div>
          <h3>Unable to Fetch Space Weather Data</h3>
          <p>NASA DONKI API is temporarily unavailable. Please try again later.</p>
        </div>
      ) : (
        <div className="no-conflicts">
          <div className="success-icon">✅</div>
          <h3>No Active Space Weather Events</h3>
          <p>Conditions are quiet - favorable for satellite communication</p>
        </div>
      )}
    </div>
  )
}

export default SpaceWeatherPanel
