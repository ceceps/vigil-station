import { useState, useEffect } from 'react'
import api from '../api/client'
import Shimmer from '../components/Shimmer'

function ConflictPanel() {
  const [conflicts, setConflicts] = useState([])
  const [passes, setPasses] = useState([])
  const [satellites, setSatellites] = useState([])
  const [groundStations, setGroundStations] = useState([])
  const [recommendations, setRecommendations] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [loadingRecommendation, setLoadingRecommendation] = useState(null)
  const [filters, setFilters] = useState({
    groundStationId: '',
    startTime: new Date().toISOString().split('T')[0],
    hours: 24
  })

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (satellites.length > 0 && groundStations.length > 0) {
      loadConflicts()
    }
  }, [filters])

  const loadInitialData = async () => {
    try {
      setLoading(true)
      const [satsData, gsData] = await Promise.all([
        api.getSatellites(),
        api.getGroundStations()
      ])
      setSatellites(satsData.satellites || [])
      setGroundStations(gsData.ground_stations || [])
      
      // Auto-load conflicts for all ground stations on initial render
      const startTime = new Date(filters.startTime + 'T00:00:00Z')
      const endTime = new Date(startTime.getTime() + filters.hours * 60 * 60 * 1000)
      
      const params = {
        start: startTime.toISOString(),
        end: endTime.toISOString()
      }
      
      const [conflictsData, passesData] = await Promise.all([
        api.getConflicts(params),
        api.getPasses(params)
      ])
      
      setConflicts(conflictsData.conflicts || [])
      setPasses(passesData.passes || [])
      
      setError(null)
    } catch (err) {
      console.error('Failed to load initial data:', err)
      setError('Failed to load satellites and ground stations')
    } finally {
      setLoading(false)
    }
  }

  const loadConflicts = async () => {
    try {
      setLoading(true)
      
      const startTime = new Date(filters.startTime + 'T00:00:00Z')
      const endTime = new Date(startTime.getTime() + filters.hours * 60 * 60 * 1000)
      
      const params = {
        start: startTime.toISOString(),
        end: endTime.toISOString()
      }
      
      if (filters.groundStationId) {
        params.ground_station_id = parseInt(filters.groundStationId)
      }
      
      // Load both conflicts and passes
      const [conflictsData, passesData] = await Promise.all([
        api.getConflicts(params),
        api.getPasses(params)
      ])
      
      setConflicts(conflictsData.conflicts || [])
      setPasses(passesData.passes || [])
      setError(null)
    } catch (err) {
      console.error('Failed to load conflicts:', err)
      setError('Failed to load conflicts')
    } finally {
      setLoading(false)
    }
  }

  const generateRecommendation = async (conflictId) => {
    try {
      setLoadingRecommendation(conflictId)
      const data = await api.generateRecommendation(conflictId)
      setRecommendations(prev => ({
        ...prev,
        [conflictId]: data.recommendation
      }))
    } catch (err) {
      console.error('Failed to generate recommendation:', err)
      setError(`Failed to generate recommendation for ${conflictId}`)
    } finally {
      setLoadingRecommendation(null)
    }
  }

  const formatDateTime = (isoString) => {
    if (!isoString) return 'N/A'
    const date = new Date(isoString)
    if (isNaN(date.getTime())) return 'Invalid Date'
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'UTC',
      timeZoneName: 'short'
    })
  }

  const getSatelliteName = (noradId) => {
    const sat = satellites.find(s => s.norad_id === noradId)
    return sat ? sat.name : `SAT-${noradId}`
  }

  const getGroundStationName = (gsId) => {
    const gs = groundStations.find(g => g.id === gsId)
    return gs ? gs.name : `GS-${gsId}`
  }

  const getPassDetails = (passId) => {
    return passes.find(p => p.id === passId)
  }

  const calculateOverlapDuration = (overlapStart, overlapEnd) => {
    if (!overlapStart || !overlapEnd) return 0
    const start = new Date(overlapStart)
    const end = new Date(overlapEnd)
    if (isNaN(start.getTime()) || isNaN(end.getTime())) return 0
    const durationMs = end - start
    return Math.round(durationMs / 60000) // minutes
  }

  const getConflictId = (conflict) => {
    // Generate conflict ID from pass IDs
    const sortedIds = [...conflict.pass_ids].sort()
    return `conflict_${sortedIds[0]}_${sortedIds[1]}`
  }

  return (
    <div className="conflict-panel">
      <div className="section-header">
        <h2>⚠️ Scheduling Conflicts</h2>
        <button onClick={loadConflicts} className="refresh-button">
          🔄 Refresh
        </button>
      </div>

      <div className="filters">
        <div className="filter-group">
          <label>Ground Station:</label>
          <select
            value={filters.groundStationId}
            onChange={(e) => setFilters({ ...filters, groundStationId: e.target.value })}
          >
            <option value="">All Ground Stations</option>
            {groundStations.map(gs => (
              <option key={gs.id} value={gs.id}>
                {gs.name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Start Date:</label>
          <input
            type="date"
            value={filters.startTime}
            onChange={(e) => setFilters({ ...filters, startTime: e.target.value })}
          />
        </div>

        <div className="filter-group">
          <label>Duration (hours):</label>
          <input
            type="number"
            min="1"
            max="168"
            value={filters.hours}
            onChange={(e) => setFilters({ ...filters, hours: parseInt(e.target.value) })}
          />
        </div>
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
      ) : (
        <>
          <div className="stats">
            <div className="stat-card">
              <div className="stat-value">{conflicts.length}</div>
              <div className="stat-label">Active Conflicts</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{passes.length}</div>
              <div className="stat-label">Total Passes</div>
            </div>
          </div>

          {conflicts.length === 0 ? (
            <div className="no-conflicts">
              <div className="success-icon">✅</div>
              <h3>No Conflicts Detected</h3>
              <p>All satellite passes are scheduled without overlaps</p>
            </div>
          ) : (
            <div className="conflicts-list">
              {conflicts.map((conflict) => {
                const conflictId = getConflictId(conflict)
                const pass1 = getPassDetails(conflict.pass_ids[0])
                const pass2 = getPassDetails(conflict.pass_ids[1])
                const overlapDuration = calculateOverlapDuration(
                  conflict.overlap_start,
                  conflict.overlap_end
                )
                const recommendation = recommendations[conflictId]

                return (
                  <div key={conflictId} className="conflict-card">
                    <div className="conflict-header">
                      <h3>⚠️ Conflict at {getGroundStationName(conflict.ground_station_id)}</h3>
                      <span className="overlap-badge">
                        {overlapDuration > 0 ? `${overlapDuration} min overlap` : 'Calculating...'}
                      </span>
                    </div>

                    <div className="conflict-details">
                      <div className="pass-info">
                        <h4>Pass 1</h4>
                        {pass1 ? (
                          <>
                            <p><strong>Satellite:</strong> {getSatelliteName(pass1.satellite_id)}</p>
                            <p><strong>Time:</strong> {formatDateTime(pass1.start_time)} - {formatDateTime(pass1.end_time)}</p>
                            <p><strong>Max Elevation:</strong> {pass1.max_elevation_deg.toFixed(1)}°</p>
                          </>
                        ) : (
                          <p>Loading pass details...</p>
                        )}
                      </div>

                      <div className="pass-info">
                        <h4>Pass 2</h4>
                        {pass2 ? (
                          <>
                            <p><strong>Satellite:</strong> {getSatelliteName(pass2.satellite_id)}</p>
                            <p><strong>Time:</strong> {formatDateTime(pass2.start_time)} - {formatDateTime(pass2.end_time)}</p>
                            <p><strong>Max Elevation:</strong> {pass2.max_elevation_deg.toFixed(1)}°</p>
                          </>
                        ) : (
                          <p>Loading pass details...</p>
                        )}
                      </div>
                    </div>

                    <div className="overlap-info">
                      <strong>Overlap Period:</strong> {formatDateTime(conflict.overlap_start)} - {formatDateTime(conflict.overlap_end)}
                    </div>

                    {!recommendation ? (
                      <button
                        className="generate-recommendation-button"
                        onClick={() => generateRecommendation(conflictId)}
                        disabled={loadingRecommendation === conflictId}
                      >
                        {loadingRecommendation === conflictId ? (
                          <>
                            <span className="spinner-small"></span> Generating AI Recommendation...
                          </>
                        ) : (
                          '🤖 Generate AI Recommendation'
                        )}
                      </button>
                    ) : (
                      <div className="recommendation">
                        <h4>🤖 AI Recommendation</h4>
                        <div className="recommendation-action">
                          <strong>Suggested Action:</strong> {recommendation.suggested_action}
                        </div>
                        {recommendation.alternative_window && (
                          <div className="alternative-window">
                            <strong>Alternative Window:</strong>
                            <p>
                              {formatDateTime(recommendation.alternative_window.start_time)} - 
                              {formatDateTime(recommendation.alternative_window.end_time)}
                            </p>
                          </div>
                        )}
                        <div className="reasoning">
                          <strong>Reasoning:</strong>
                          <p>{recommendation.reasoning}</p>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default ConflictPanel