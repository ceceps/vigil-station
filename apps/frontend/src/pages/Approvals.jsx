import { useState, useEffect } from 'react'
import api from '../api/client'
import Shimmer from '../components/Shimmer'

function Approvals() {
  const [conflicts, setConflicts] = useState([])
  const [passes, setPasses] = useState([])
  const [satellites, setSatellites] = useState([])
  const [groundStations, setGroundStations] = useState([])
  const [recommendations, setRecommendations] = useState({})
  const [approvals, setApprovals] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [processingApproval, setProcessingApproval] = useState(null)
  const [loadingRecommendation, setLoadingRecommendation] = useState(null)
  const [filterStatus, setFilterStatus] = useState('all') // 'all' | 'pending' | 'approved' | 'overridden'

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      
      const startTime = new Date()
      const endTime = new Date(startTime.getTime() + 24 * 60 * 60 * 1000)
      
      const params = {
        start: startTime.toISOString(),
        end: endTime.toISOString()
      }
      
      const [satsData, gsData, conflictsData, passesData, analyticsData] = await Promise.all([
        api.getSatellites(),
        api.getGroundStations(),
        api.getConflicts(params),
        api.getPasses(params),
        api.getAnalyticsInsights().catch(() => ({}))
      ])
      
      setSatellites(satsData.satellites || [])
      setGroundStations(gsData.ground_stations || [])
      setConflicts(conflictsData.conflicts || [])
      setPasses(passesData.passes || [])

      // Hydrate recommendations from DB history
      const initialRecs = {}
      const recList = analyticsData.recommendations_history || []
      recList.forEach(r => {
        if (r.conflict_id) {
          initialRecs[r.conflict_id] = r
        }
      })
      setRecommendations(initialRecs)

      // Hydrate approvals from DB history
      const initialApprovals = {}
      const schedList = analyticsData.schedules_history || []
      schedList.forEach(s => {
        const matchingRec = recList.find(r => r.target_pass_id === s.id || r.conflict_id === s.id)
        if (matchingRec) {
          initialApprovals[matchingRec.conflict_id] = {
            status: s.approved ? 'approved' : 'overridden',
            override_reason: s.override_reason
          }
        }
      })
      setApprovals(initialApprovals)

      setError(null)
    } catch (err) {
      console.error('Failed to load data:', err)
      setError('Failed to load approval data')
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

  const handleApprove = async (conflictId, targetPassId) => {
    try {
      setProcessingApproval(conflictId)
      await api.approveSchedule(targetPassId, true)
      setApprovals(prev => ({
        ...prev,
        [conflictId]: { status: 'approved', passId: targetPassId }
      }))
      setError(null)
    } catch (err) {
      console.error('Failed to approve:', err)
      setError(`Failed to approve schedule for ${conflictId}`)
    } finally {
      setProcessingApproval(null)
    }
  }

  const handleOverride = async (conflictId, targetPassId, reason) => {
    if (!reason || reason.trim() === '') {
      setError('Override reason is required')
      return
    }

    try {
      setProcessingApproval(conflictId)
      await api.approveSchedule(targetPassId, false, reason)
      setApprovals(prev => ({
        ...prev,
        [conflictId]: { status: 'overridden', passId: targetPassId, reason }
      }))
      setError(null)
    } catch (err) {
      console.error('Failed to override:', err)
      setError(`Failed to override schedule for ${conflictId}`)
    } finally {
      setProcessingApproval(null)
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
    const rawName = sat ? sat.name : `SAT-${noradId}`
    return rawName.replace(/^0\s+/, '')
  }

  const getGroundStationName = (gsId) => {
    const gs = groundStations.find(g => g.id === gsId)
    return gs ? gs.name : `GS-${gsId}`
  }

  const getPassDetails = (passId) => {
    return passes.find(p => p.id === passId)
  }

  const getConflictId = (conflict) => {
    const sortedIds = [...conflict.pass_ids].sort()
    return `conflict_${sortedIds[0]}_${sortedIds[1]}`
  }

  return (
    <div className="approvals">
      <div className="section-header">
        <h2>✅ Approval Dashboard</h2>
        <button onClick={loadData} className="refresh-button">
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
      ) : (
        <>
          <div className="stats">
            <div className="stat-card">
              <div className="stat-value">
                {conflicts.filter(c => !approvals[getConflictId(c)]).length}
              </div>
              <div className="stat-label">Pending Approvals</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">
                {Object.values(approvals).filter(a => a.status === 'approved').length}
              </div>
              <div className="stat-label">Approved</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">
                {Object.values(approvals).filter(a => a.status === 'overridden').length}
              </div>
              <div className="stat-label">Overridden</div>
            </div>
          </div>

          <div className="filters" style={{ marginBottom: '1.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button
              type="button"
              className={`refresh-button ${filterStatus === 'all' ? 'active' : ''}`}
              style={{ opacity: filterStatus === 'all' ? 1 : 0.7 }}
              onClick={() => setFilterStatus('all')}
            >
              All ({conflicts.length})
            </button>
            <button
              type="button"
              className={`refresh-button ${filterStatus === 'pending' ? 'active' : ''}`}
              style={{ opacity: filterStatus === 'pending' ? 1 : 0.7 }}
              onClick={() => setFilterStatus('pending')}
            >
              ⏳ Pending ({conflicts.filter(c => !approvals[getConflictId(c)]).length})
            </button>
            <button
              type="button"
              className={`refresh-button ${filterStatus === 'approved' ? 'active' : ''}`}
              style={{ opacity: filterStatus === 'approved' ? 1 : 0.7 }}
              onClick={() => setFilterStatus('approved')}
            >
              ✅ Approved ({Object.values(approvals).filter(a => a.status === 'approved').length})
            </button>
            <button
              type="button"
              className={`refresh-button ${filterStatus === 'overridden' ? 'active' : ''}`}
              style={{ opacity: filterStatus === 'overridden' ? 1 : 0.7 }}
              onClick={() => setFilterStatus('overridden')}
            >
              ⚠️ Overridden ({Object.values(approvals).filter(a => a.status === 'overridden').length})
            </button>
          </div>

          {conflicts.filter(c => {
            const cid = getConflictId(c)
            const app = approvals[cid]
            if (filterStatus === 'pending') return !app
            if (filterStatus === 'approved') return app?.status === 'approved'
            if (filterStatus === 'overridden') return app?.status === 'overridden'
            return true
          }).length === 0 ? (
            <div className="no-conflicts">
              <div className="success-icon">✅</div>
              <h3>No Approvals in Selected Filter</h3>
              <p>No conflicts match status "{filterStatus}"</p>
            </div>
          ) : (
            <div className="approvals-list">
              {conflicts
                .filter(c => {
                  const cid = getConflictId(c)
                  const app = approvals[cid]
                  if (filterStatus === 'pending') return !app
                  if (filterStatus === 'approved') return app?.status === 'approved'
                  if (filterStatus === 'overridden') return app?.status === 'overridden'
                  return true
                })
                .map((conflict) => {
                const conflictId = getConflictId(conflict)
                const pass1 = getPassDetails(conflict.pass_ids[0])
                const pass2 = getPassDetails(conflict.pass_ids[1])
                const recommendation = recommendations[conflictId]
                const approval = approvals[conflictId]

                return (
                  <div key={conflictId} className="approval-card">
                    <div className="approval-header">
                      <h3>Conflict at {getGroundStationName(conflict.ground_station_id)}</h3>
                      {approval && (
                        <span className={`status-badge ${approval.status}`}>
                          {approval.status === 'approved' ? '✅ Approved' : '⚠️ Overridden'}
                        </span>
                      )}
                    </div>

                    <div className="conflict-summary">
                      <div className="pass-summary">
                        <strong>Pass 1:</strong> {pass1 && getSatelliteName(pass1.satellite_id)}
                        <br />
                        <small>{pass1 && formatDateTime(pass1.start_time)}</small>
                      </div>
                      <div className="pass-summary">
                        <strong>Pass 2:</strong> {pass2 && getSatelliteName(pass2.satellite_id)}
                        <br />
                        <small>{pass2 && formatDateTime(pass2.start_time)}</small>
                      </div>
                    </div>

                    {!recommendation ? (
                      <button
                        className="generate-recommendation-button"
                        onClick={() => generateRecommendation(conflictId)}
                        disabled={loadingRecommendation === conflictId}
                      >
                        {loadingRecommendation === conflictId ? (
                          <>
                            <span className="spinner-small"></span> Generating Recommendation...
                          </>
                        ) : (
                          '🤖 Generate Recommendation First'
                        )}
                      </button>
                    ) : (
                      <>
                        <div className="recommendation-summary">
                          <h4>🤖 AI Recommendation</h4>
                          <p><strong>Action:</strong> {recommendation.suggested_action}</p>
                          {recommendation.alternative_window && (
                            <p>
                              <strong>Alternative:</strong> {formatDateTime(recommendation.alternative_window.start_time)}
                            </p>
                          )}
                          <p className="reasoning-text">{recommendation.reasoning}</p>
                        </div>

                        {!approval ? (
                          <div className="approval-actions">
                            <button
                              className="approve-button"
                              onClick={() => handleApprove(conflictId, recommendation.target_pass_id)}
                              disabled={processingApproval === conflictId}
                            >
                              {processingApproval === conflictId ? (
                                <>
                                  <span className="spinner-small"></span> Processing...
                                </>
                              ) : (
                                '✅ Approve Recommendation'
                              )}
                            </button>
                            <button
                              className="override-button"
                              onClick={() => {
                                const reason = prompt('Enter override reason:')
                                if (reason) {
                                  handleOverride(conflictId, recommendation.target_pass_id, reason)
                                }
                              }}
                              disabled={processingApproval === conflictId}
                            >
                              ⚠️ Override
                            </button>
                          </div>
                        ) : (
                          <div className="approval-result">
                            <p>
                              <strong>Decision:</strong> {approval.status}
                            </p>
                            {approval.reason && (
                              <p>
                                <strong>Reason:</strong> {approval.reason}
                              </p>
                            )}
                            <p className="timestamp">
                              <small>Processed at {new Date().toLocaleString()}</small>
                            </p>
                          </div>
                        )}
                      </>
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

export default Approvals
