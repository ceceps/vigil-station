import { useState, useEffect } from 'react'
import ScheduleTable from './pages/ScheduleTable'
import ConflictPanel from './pages/ConflictPanel'
import Approvals from './pages/Approvals'
import SpaceWeatherPanel from './pages/SpaceWeatherPanel'
import LeafletMap from './components/LeafletMap'

function App() {
  const [activeTab, setActiveTab] = useState('schedule')
  const [satellites, setSatellites] = useState([])
  const [groundStations, setGroundStations] = useState([])
  const [passes, setPasses] = useState([])
  const [loading, setLoading] = useState(true)
  const [theme, setTheme] = useState(() => {
    // Load theme from localStorage or default to 'light'
    return localStorage.getItem('theme') || 'light'
  })

  useEffect(() => {
    // Apply theme to document
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

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

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'light' ? 'dark' : 'light')
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div>
            <h1>🛰️ Mission Planning Assistant</h1>
            <p className="subtitle">Ground Station Contact Scheduling with AI Decision-Support</p>
          </div>
          <button 
            className="theme-toggle" 
            onClick={toggleTheme}
            aria-label="Toggle theme"
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>
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
        <button
          className={`nav-button ${activeTab === 'map' ? 'active' : ''}`}
          onClick={() => setActiveTab('map')}
        >
          🗺️ Map
        </button>
        <button
          className={`nav-button ${activeTab === 'space-weather' ? 'active' : ''}`}
          onClick={() => setActiveTab('space-weather')}
        >
          🌞 Space Weather
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
            {activeTab === 'map' && (
              <div className="map-panel">
                <div className="section-header">
                  <h2>🗺️ Ground Station & Satellite Map</h2>
                </div>
                <LeafletMap 
                  groundStations={groundStations} 
                  satellites={satellites}
                  passes={passes}
                />
              </div>
            )}
            {activeTab === 'space-weather' && <SpaceWeatherPanel />}
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