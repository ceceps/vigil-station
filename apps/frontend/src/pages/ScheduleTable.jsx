import { useState, useEffect } from 'react'
import api from '../api/client'
import Shimmer from '../components/Shimmer'

function ScheduleTable() {
  const [passes, setPasses] = useState([])
  const [satellites, setSatellites] = useState([])
  const [groundStations, setGroundStations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState({
    satelliteId: '',
    groundStationId: '',
    startTime: new Date().toISOString().split('T')[0],
    hours: 24
  })

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (satellites.length > 0 && groundStations.length > 0) {
      loadPasses()
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
      
      // Auto-load passes for all satellites on initial render
      const startTime = new Date(filters.startTime + 'T00:00:00Z')
      const endTime = new Date(startTime.getTime() + filters.hours * 60 * 60 * 1000)
      
      const passesData = await api.getPasses({
        start: startTime.toISOString(),
        end: endTime.toISOString()
      })
      setPasses(passesData.passes || [])
      
      setError(null)
    } catch (err) {
      console.error('Failed to load initial data:', err)
      setError('Failed to load satellites and ground stations')
    } finally {
      setLoading(false)
    }
  }

  const loadPasses = async () => {
    try {
      setLoading(true)
      
      const startTime = new Date(filters.startTime + 'T00:00:00Z')
      const endTime = new Date(startTime.getTime() + filters.hours * 60 * 60 * 1000)
      
      const params = {
        start: startTime.toISOString(),
        end: endTime.toISOString()
      }
      
      if (filters.satelliteId) {
        params.satellite_id = parseInt(filters.satelliteId)
      }
      
      if (filters.groundStationId) {
        params.ground_station_id = parseInt(filters.groundStationId)
      }
      
      const data = await api.getPasses(params)
      setPasses(data.passes || [])
      setError(null)
    } catch (err) {
      console.error('Failed to load passes:', err)
      setError('Failed to load pass windows')
    } finally {
      setLoading(false)
    }
  }

  const formatDateTime = (isoString) => {
    const date = new Date(isoString)
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

  const getElevationColor = (elevation) => {
    if (elevation >= 45) return '#4caf50'
    if (elevation >= 30) return '#ff9800'
    return '#f44336'
  }

  return (
    <div className="schedule-table">
      <div className="section-header">
        <h2>📅 Satellite Pass Schedule</h2>
        <button onClick={loadPasses} className="refresh-button">
          🔄 Refresh
        </button>
      </div>

      <div className="filters">
        <div className="filter-group">
          <label>Satellite:</label>
          <select
            value={filters.satelliteId}
            onChange={(e) => setFilters({ ...filters, satelliteId: e.target.value })}
          >
            <option value="">All Satellites</option>
            {satellites.map(sat => (
              <option key={sat.norad_id} value={sat.norad_id}>
                {sat.name}
              </option>
            ))}
          </select>
        </div>

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
          <Shimmer type="table" rows={8} />
        </>
      ) : (
        <>
          <div className="stats">
            <div className="stat-card">
              <div className="stat-value">{passes.length}</div>
              <div className="stat-label">Total Passes</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{satellites.length}</div>
              <div className="stat-label">Satellites</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{groundStations.length}</div>
              <div className="stat-label">Ground Stations</div>
            </div>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Satellite</th>
                  <th>Ground Station</th>
                  <th>Start Time</th>
                  <th>End Time</th>
                  <th>Max Elevation</th>
                  <th>Duration</th>
                </tr>
              </thead>
              <tbody>
                {passes.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="no-data">
                      No passes found for the selected criteria
                    </td>
                  </tr>
                ) : (
                  passes.map((pass) => {
                    const startTime = new Date(pass.start_time)
                    const endTime = new Date(pass.end_time)
                    const durationMinutes = Math.round((endTime - startTime) / 60000)
                    
                    return (
                      <tr key={pass.id}>
                        <td>{getSatelliteName(pass.satellite_id)}</td>
                        <td>{getGroundStationName(pass.ground_station_id)}</td>
                        <td>{formatDateTime(pass.start_time)}</td>
                        <td>{formatDateTime(pass.end_time)}</td>
                        <td>
                          <span
                            className="elevation-badge"
                            style={{ backgroundColor: getElevationColor(pass.max_elevation_deg) }}
                          >
                            {pass.max_elevation_deg.toFixed(1)}°
                          </span>
                        </td>
                        <td>{durationMinutes} min</td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}

export default ScheduleTable
