import { useEffect, useState, useRef, useCallback } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import api from '../api/client'

function LeafletMap() {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const gsMarkersRef = useRef([])
  const satMarkersRef = useRef([])
  const passLinesRef = useRef([])
  const satPositionsRef = useRef({})
  const animFrameRef = useRef(null)
  const [mapReady, setMapReady] = useState(false)

  const stationIcon = L.divIcon({
    className: 'custom-marker',
    html: `<div style="width:18px;height:18px;background:#4caf50;border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:2px solid white;box-shadow:0 0 8px rgba(76,175,80,0.6);"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
    popupAnchor: [0, -10]
  })

  const satIcon = L.divIcon({
    className: 'custom-marker',
    html: `<div style="width:14px;height:14px;background:#2196f3;border-radius:50%;border:2px solid white;box-shadow:0 0 8px rgba(33,150,243,0.6);"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
    popupAnchor: [0, -8]
  })

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return

    const map = L.map(mapRef.current, {
      center: [-6.2088, 106.8456],
      zoom: 5,
      zoomControl: true,
      scrollWheelZoom: true
    })

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
      maxZoom: 19
    }).addTo(map)

    mapInstanceRef.current = map
    setMapReady(true)

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
      map.remove()
      mapInstanceRef.current = null
      setMapReady(false)
    }
  }, [])

  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map || !mapReady) return

    let cancelled = false
    let satellites = []
    let passes = []

    const loadData = async () => {
      try {
        const now = new Date()
        const end = new Date(now.getTime() + 24 * 60 * 60 * 1000)
        
        const [gsData, satsData, passesData] = await Promise.all([
          api.getGroundStations(),
          api.getSatellites(),
          api.getPasses({
            start: now.toISOString(),
            end: end.toISOString()
          })
        ])

        if (cancelled) return

        const groundStations = gsData.ground_stations || []
        satellites = satsData.satellites || []
        passes = passesData.passes || []

        const bounds = []
        groundStations.forEach(gs => {
          const marker = L.marker([gs.lat, gs.lon], { icon: stationIcon })
            .addTo(map)
            .bindPopup(`
              <div class="popup-content">
                <strong>📡 ${gs.name}</strong><br/>
                Lat: ${gs.lat.toFixed(4)}°<br/>
                Lon: ${gs.lon.toFixed(4)}°<br/>
                Min Elevation: ${gs.min_elevation_deg}°
              </div>
            `)
          gsMarkersRef.current.push(marker)
          bounds.push([gs.lat, gs.lon])
        })

        if (bounds.length > 0) {
          map.fitBounds(bounds, { padding: [50, 50] })
        }

        const animate = () => {
          if (cancelled) return

          const time = Date.now() / 1000

          satMarkersRef.current.forEach(m => map.removeLayer(m))
          satMarkersRef.current = []

          satellites.forEach((sat, i) => {
            const orbitSpeed = 0.0005
            const orbitOffset = (i * Math.PI * 2) / satellites.length
            const lon = ((time * orbitSpeed + orbitOffset) * 50) % 360 - 180
            const lat = Math.sin(time * orbitSpeed + orbitOffset) * 60

            satPositionsRef.current[sat.norad_id] = { lat, lon }

            const marker = L.marker([lat, lon], { icon: satIcon })
              .addTo(map)
              .bindPopup(`
                <div class="popup-content">
                  <strong>🛰️ ${sat.name}</strong><br/>
                  NORAD ID: ${sat.norad_id}<br/>
                  Group: ${sat.group}<br/>
                  Lat: ${lat.toFixed(2)}°<br/>
                  Lon: ${lon.toFixed(2)}°
                </div>
              `, { className: 'satellite-popup' })
            satMarkersRef.current.push(marker)
          })

          // Clear old pass lines
          passLinesRef.current.forEach(p => map.removeLayer(p))
          passLinesRef.current = []

          // Draw active pass lines
          passes.slice(0, 10).forEach(pass => {
            const gs = groundStations.find(g => g.id === pass.ground_station_id)
            const satPos = satPositionsRef.current[pass.satellite_id]
            
            if (gs && satPos) {
              const line = L.polyline(
                [[gs.lat, gs.lon], [satPos.lat, satPos.lon]],
                {
                  color: '#ff9800',
                  weight: 2,
                  dashArray: '8, 6',
                  opacity: 0.8
                }
              ).addTo(map)
              passLinesRef.current.push(line)
            }
          })

          animFrameRef.current = requestAnimationFrame(animate)
        }

        animate()
      } catch (err) {
        console.error('Failed to load map data:', err)
      }
    }

    loadData()

    return () => {
      cancelled = true
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
      gsMarkersRef.current.forEach(m => map.removeLayer(m))
      gsMarkersRef.current = []
      satMarkersRef.current.forEach(m => map.removeLayer(m))
      satMarkersRef.current = []
      passLinesRef.current.forEach(p => map.removeLayer(p))
      passLinesRef.current = []
    }
  }, [mapReady])

  return (
    <div className="leaflet-map-wrapper">
      <div ref={mapRef} className="leaflet-map-container" />
      <div className="map-legend">
        <div className="legend-item">
          <span className="legend-icon station"></span>
          <span>Ground Station</span>
        </div>
        <div className="legend-item">
          <span className="legend-icon satellite"></span>
          <span>Satellite</span>
        </div>
        <div className="legend-item">
          <span className="legend-icon pass-line"></span>
          <span>Pass Window</span>
        </div>
      </div>
    </div>
  )
}

export default LeafletMap
