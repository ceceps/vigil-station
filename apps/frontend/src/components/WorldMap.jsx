import { useRef, useEffect, useState, useCallback } from 'react'
import api from '../api/client'

const WORLD_MAP_URL = 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/World_map_blank_without_borders.svg/1280px-World_map_blank_without_borders.svg.png'

function WorldMap({ groundStations: propGS = [], satellites: propSats = [], passes: propPasses = [] }) {
  const canvasRef = useRef(null)
  const mapImageRef = useRef(null)
  const [hoveredItem, setHoveredItem] = useState(null)
  const [groundStations, setGroundStations] = useState(propGS)
  const [satellites, setSatellites] = useState(propSats)
  const [passes, setPasses] = useState(propPasses)
  const [mapLoaded, setMapLoaded] = useState(false)

  // Zoom & pan state
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

  const WIDTH = 1000
  const HEIGHT = 500

  // Load world map image
  useEffect(() => {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      mapImageRef.current = img
      setMapLoaded(true)
    }
    img.onerror = () => {
      console.warn('Failed to load world map image, using outline fallback')
      setMapLoaded(false)
    }
    img.src = WORLD_MAP_URL
  }, [])

  // Load data
  useEffect(() => {
    const loadData = async () => {
      try {
        const [gsData, satsData] = await Promise.all([
          api.getGroundStations(),
          api.getSatellites()
        ])
        setGroundStations(gsData.ground_stations || [])
        setSatellites(satsData.satellites || [])

        const now = new Date()
        const end = new Date(now.getTime() + 24 * 60 * 60 * 1000)
        const passesData = await api.getPasses({
          start: now.toISOString(),
          end: end.toISOString()
        })
        setPasses(passesData.passes || [])
      } catch (err) {
        console.error('Failed to load map data:', err)
      }
    }
    if (propGS.length === 0) loadData()
  }, [])

  // Draw map
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    canvas.width = WIDTH
    canvas.height = HEIGHT

    // Clear
    ctx.fillStyle = '#0a1628'
    ctx.fillRect(0, 0, WIDTH, HEIGHT)

    // Apply zoom & pan
    ctx.save()
    ctx.translate(pan.x, pan.y)
    ctx.scale(zoom, zoom)

    // Draw world map background
    if (mapImageRef.current && mapLoaded) {
      ctx.drawImage(mapImageRef.current, 0, 0, WIDTH, HEIGHT)
    } else {
      drawWorldOutline(ctx, WIDTH, HEIGHT)
    }

    // Draw grid
    drawGrid(ctx, WIDTH, HEIGHT)

    // Draw ground stations
    groundStations.forEach(gs => {
      const { x, y } = latLonToXY(gs.lat, gs.lon, WIDTH, HEIGHT)
      drawGroundStation(ctx, x, y, gs.name)
    })

    // Draw satellites
    if (satellites.length > 0) {
      const time = Date.now() / 1000
      satellites.forEach((sat, index) => {
        const orbitSpeed = 0.0005
        const orbitOffset = (index * Math.PI * 2) / satellites.length
        const satLon = ((time * orbitSpeed + orbitOffset) * 50) % 360 - 180
        const satLat = Math.sin(time * orbitSpeed + orbitOffset) * 60
        const { x, y } = latLonToXY(satLat, satLon, WIDTH, HEIGHT)
        drawSatellite(ctx, x, y, sat.name || `SAT-${sat.norad_id}`)
      })
    }

    // Draw pass lines
    if (passes.length > 0 && satellites.length > 0) {
      passes.slice(0, 10).forEach(pass => {
        const gs = groundStations.find(g => g.id === pass.ground_station_id)
        const sat = satellites.find(s => s.norad_id === pass.satellite_id)
        if (gs && sat) {
          const gsPos = latLonToXY(gs.lat, gs.lon, WIDTH, HEIGHT)
          const passTime = new Date(pass.start_time).getTime() / 1000
          const orbitSpeed = 0.0005
          const satLon = ((passTime * orbitSpeed) * 50) % 360 - 180
          const satLat = Math.sin(passTime * orbitSpeed) * 60
          const satPos = latLonToXY(satLat, satLon, WIDTH, HEIGHT)
          drawPassLine(ctx, gsPos.x, gsPos.y, satPos.x, satPos.y)
        }
      })
    }

    ctx.restore()

    // Draw legend (outside zoom)
    drawLegend(ctx, WIDTH, HEIGHT)

  }, [groundStations, satellites, passes, zoom, pan, mapLoaded, hoveredItem])

  // Mouse handlers for pan
  const handleMouseDown = (e) => {
    setIsDragging(true)
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y })
  }

  const handleMouseMove = (e) => {
    const canvas = canvasRef.current
    if (!canvas) return

    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      })
      return
    }

    // Check hover
    const rect = canvas.getBoundingClientRect()
    const scaleX = WIDTH / rect.width
    const scaleY = HEIGHT / rect.height
    const x = (e.clientX - rect.left) * scaleX
    const y = (e.clientY - rect.top) * scaleY

    let found = null
    groundStations.forEach(gs => {
      const pos = latLonToXY(gs.lat, gs.lon, WIDTH, HEIGHT)
      const dx = (x - pan.x) / zoom - pos.x
      const dy = (y - pan.y) / zoom - pos.y
      const distance = Math.sqrt(dx * dx + dy * dy)
      if (distance < 15) {
        found = { type: 'groundStation', name: gs.name, lat: gs.lat, lon: gs.lon }
      }
    })

    setHoveredItem(found)
  }

  const handleMouseUp = () => setIsDragging(false)

  // Zoom handlers
  const handleZoomIn = () => setZoom(z => Math.min(z * 1.3, 5))
  const handleZoomOut = () => setZoom(z => Math.max(z / 1.3, 0.5))
  const handleReset = () => { setZoom(1); setPan({ x: 0, y: 0 }) }

  // Mouse wheel zoom
  const handleWheel = (e) => {
    e.preventDefault()
    if (e.deltaY < 0) {
      handleZoomIn()
    } else {
      handleZoomOut()
    }
  }

  return (
    <div className="world-map-wrapper">
      <div className="map-controls">
        <button onClick={handleZoomIn} title="Zoom In">+</button>
        <button onClick={handleZoomOut} title="Zoom Out">−</button>
        <button onClick={handleReset} title="Reset View">⌂</button>
        <span className="zoom-level">{Math.round(zoom * 100)}%</span>
      </div>
      <div className="world-map-container">
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={() => { setIsDragging(false); setHoveredItem(null) }}
          onWheel={handleWheel}
          style={{ cursor: isDragging ? 'grabbing' : (hoveredItem ? 'pointer' : 'grab') }}
        />
        {hoveredItem && (
          <div className="map-tooltip">
            <strong>{hoveredItem.name}</strong>
            {hoveredItem.type === 'groundStation' && (
              <span> ({hoveredItem.lat.toFixed(2)}°, {hoveredItem.lon.toFixed(2)}°)</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function latLonToXY(lat, lon, width, height) {
  const x = ((lon + 180) / 360) * width
  const y = ((90 - lat) / 180) * height
  return { x, y }
}

function drawGrid(ctx, width, height) {
  ctx.strokeStyle = 'rgba(100, 150, 255, 0.1)'
  ctx.lineWidth = 0.5

  for (let lat = -60; lat <= 60; lat += 30) {
    const y = ((90 - lat) / 180) * height
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(width, y)
    ctx.stroke()
  }

  for (let lon = -180; lon <= 180; lon += 60) {
    const x = ((lon + 180) / 360) * width
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, height)
    ctx.stroke()
  }
}

function drawWorldOutline(ctx, width, height) {
  ctx.strokeStyle = '#2a4a7f'
  ctx.lineWidth = 1
  ctx.fillStyle = 'rgba(30, 60, 100, 0.3)'

  const continents = [
    [[-130, 50], [-120, 60], [-100, 60], [-80, 50], [-60, 40], [-80, 25], [-100, 20], [-120, 30], [-130, 50]],
    [[-80, 10], [-60, 0], [-50, -10], [-60, -30], [-70, -40], [-80, -20], [-80, 10]],
    [[-10, 40], [0, 50], [20, 55], [40, 50], [50, 40], [30, 35], [10, 35], [-10, 40]],
    [[-10, 35], [10, 30], [30, 20], [40, 0], [30, -20], [20, -30], [10, -20], [0, 0], [-10, 10], [-10, 35]],
    [[40, 50], [60, 60], [80, 55], [100, 50], [120, 40], [140, 35], [130, 20], [100, 10], [80, 15], [60, 25], [40, 30], [40, 50]],
    [[110, -15], [130, -15], [150, -20], [150, -35], [130, -35], [110, -25], [110, -15]]
  ]

  continents.forEach(continent => {
    ctx.beginPath()
    continent.forEach((point, i) => {
      const { x, y } = latLonToXY(point[1], point[0], width, height)
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    })
    ctx.closePath()
    ctx.fill()
    ctx.stroke()
  })
}

function drawGroundStation(ctx, x, y, name) {
  // Glow
  ctx.shadowColor = '#4caf50'
  ctx.shadowBlur = 8

  // Triangle
  ctx.fillStyle = '#4caf50'
  ctx.beginPath()
  ctx.moveTo(x, y - 10)
  ctx.lineTo(x - 7, y + 5)
  ctx.lineTo(x + 7, y + 5)
  ctx.closePath()
  ctx.fill()

  ctx.shadowBlur = 0

  // Label
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 11px Arial'
  ctx.textAlign = 'center'
  ctx.fillText(name.split(' ')[0], x, y + 20)
}

function drawSatellite(ctx, x, y, name) {
  // Glow
  ctx.shadowColor = '#2196f3'
  ctx.shadowBlur = 12

  // Diamond
  ctx.fillStyle = '#2196f3'
  ctx.beginPath()
  ctx.moveTo(x, y - 7)
  ctx.lineTo(x + 5, y)
  ctx.lineTo(x, y + 7)
  ctx.lineTo(x - 5, y)
  ctx.closePath()
  ctx.fill()

  ctx.shadowBlur = 0

  // Small label
  ctx.fillStyle = '#90caf9'
  ctx.font = '9px Arial'
  ctx.textAlign = 'center'
  ctx.fillText(name.split(' ').slice(-1)[0], x, y - 10)
}

function drawPassLine(ctx, x1, y1, x2, y2) {
  ctx.strokeStyle = '#ff9800'
  ctx.lineWidth = 2
  ctx.setLineDash([6, 4])
  ctx.shadowColor = '#ff9800'
  ctx.shadowBlur = 4

  ctx.beginPath()
  ctx.moveTo(x1, y1)
  ctx.lineTo(x2, y2)
  ctx.stroke()

  ctx.setLineDash([])
  ctx.shadowBlur = 0
}

function drawLegend(ctx, width, height) {
  const legendX = 10
  const legendY = height - 90
  const legendWidth = 130
  const legendHeight = 80

  ctx.fillStyle = 'rgba(10, 22, 40, 0.85)'
  ctx.fillRect(legendX, legendY, legendWidth, legendHeight)
  ctx.strokeStyle = '#2a4a7f'
  ctx.lineWidth = 1
  ctx.strokeRect(legendX, legendY, legendWidth, legendHeight)

  ctx.font = '11px Arial'
  ctx.textAlign = 'left'

  // Ground Station
  ctx.fillStyle = '#4caf50'
  ctx.beginPath()
  ctx.moveTo(legendX + 15, legendY + 12)
  ctx.lineTo(legendX + 10, legendY + 22)
  ctx.lineTo(legendX + 20, legendY + 22)
  ctx.closePath()
  ctx.fill()
  ctx.fillStyle = '#ffffff'
  ctx.fillText('Ground Station', legendX + 28, legendY + 20)

  // Satellite
  ctx.fillStyle = '#2196f3'
  ctx.beginPath()
  ctx.moveTo(legendX + 15, legendY + 32)
  ctx.lineTo(legendX + 20, legendY + 37)
  ctx.lineTo(legendX + 15, legendY + 42)
  ctx.lineTo(legendX + 10, legendY + 37)
  ctx.closePath()
  ctx.fill()
  ctx.fillStyle = '#ffffff'
  ctx.fillText('Satellite', legendX + 28, legendY + 40)

  // Pass Window
  ctx.strokeStyle = '#ff9800'
  ctx.lineWidth = 2
  ctx.setLineDash([4, 3])
  ctx.beginPath()
  ctx.moveTo(legendX + 10, legendY + 55)
  ctx.lineTo(legendX + 22, legendY + 55)
  ctx.stroke()
  ctx.setLineDash([])
  ctx.fillStyle = '#ffffff'
  ctx.fillText('Pass Window', legendX + 28, legendY + 59)

  // Zoom info
  ctx.fillStyle = '#888888'
  ctx.font = '9px Arial'
  ctx.fillText('Scroll to zoom, drag to pan', legendX + 5, legendY + 74)
}

export default WorldMap
