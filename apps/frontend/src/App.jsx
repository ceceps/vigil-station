import { useState, useEffect } from 'react'
import ScheduleTable from './pages/ScheduleTable'
import ConflictPanel from './pages/ConflictPanel'
import Approvals from './pages/Approvals'

function App() {
  const [activeTab, setActiveTab] = useState('schedule')
  const [satellites, setSatellites] = useState([])
  const [groundStations, setGroundStations] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Load initial data
    const loadInitialData = async () => {
      try {
        setLoading(true)
        // Data will be loaded by individual components
        setLoading(false)
      } catch (error) {
        console.error('Failed to load initial data:', error)
        setLoading(false)
      }
    }

    loadInitialData()
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <h1>🛰️ Mission Planning Assistant</h1>
        <p className="subtitle">Ground Station Contact Scheduling with AI Decision-Support</p>
      </header>

      <nav className="app-nav">
        <button
          className={`nav-button ${activeTab === 'schedule' ? 'active' : ''}`}
          onClick={() => setActiveTab('schedule')}
        >
          📅 Schedule
        </button>
        <button
          className={`nav-button ${activeTab === 'conflicts' ? 'active' : ''}`}
          onClick={() => setActiveTab('conflicts')}
        >
          ⚠️ Conflicts
        </button>
        <button
          className={`nav-button ${activeTab === 'approvals' ? 'active' : ''}`}
          onClick={() => setActiveTab('approvals')}
        >
          ✅ Approvals
        </button>
      </nav>

      <main className="app-main">
        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Loading...</p>
          </div>
        ) : (
          <>
            {activeTab === 'schedule' && <ScheduleTable />}
            {activeTab === 'conflicts' && <ConflictPanel />}
            {activeTab === 'approvals' && <Approvals />}
          </>
        )}
      </main>

      <footer className="app-footer">
        <p>Mission Planning Assistant v1.0.0 | IBM Bob Space Exploration Hackathon</p>
      </footer>
    </div>
  )
}

export default App
