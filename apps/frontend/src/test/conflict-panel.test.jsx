import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import ConflictPanel from '../pages/ConflictPanel'
import api from '../api/client'

vi.mock('../api/client', () => ({
  default: {
    getSatellites: vi.fn(),
    getGroundStations: vi.fn(),
    getConflicts: vi.fn(),
    getPasses: vi.fn(),
    generateRecommendation: vi.fn()
  }
}))

describe('ConflictPanel', () => {
  const mockSatellites = {
    satellites: [
      { norad_id: 43569, name: 'IRIDIUM 160', group: 'iridium' },
      { norad_id: 43570, name: 'IRIDIUM 166', group: 'iridium' }
    ]
  }

  const mockGroundStations = {
    ground_stations: [{ id: 1, name: 'Jakarta', lat: -6.2088, lon: 106.8456, min_elevation_deg: 10 }]
  }

  const mockPasses = {
    passes: [
      { id: 'pass_1', satellite_id: 43569, ground_station_id: 1, start_time: '2024-01-01T10:00:00Z', end_time: '2024-01-01T10:10:00Z', max_elevation_deg: 45.5 },
      { id: 'pass_2', satellite_id: 43570, ground_station_id: 1, start_time: '2024-01-01T10:05:00Z', end_time: '2024-01-01T10:15:00Z', max_elevation_deg: 38.2 }
    ]
  }

  const mockConflicts = {
    conflicts: [{
      ground_station_id: 1,
      pass_ids: ['pass_1', 'pass_2'],
      overlap_start: '2024-01-01T10:05:00Z',
      overlap_end: '2024-01-01T10:10:00Z'
    }]
  }

  beforeEach(() => {
    vi.clearAllMocks()
    api.getSatellites.mockResolvedValue(mockSatellites)
    api.getGroundStations.mockResolvedValue(mockGroundStations)
    api.getPasses.mockResolvedValue(mockPasses)
    api.getConflicts.mockResolvedValue(mockConflicts)
    api.generateRecommendation.mockResolvedValue({
      recommendation: { suggested_action: 'reschedule', reasoning: 'Overlap detected' }
    })
  })

  it('renders header after loading', async () => {
    render(<ConflictPanel />)
    await waitFor(() => {
      expect(screen.getByText(/Scheduling Conflicts/)).toBeTruthy()
    })
  })

  it('renders stat cards', async () => {
    render(<ConflictPanel />)
    await waitFor(() => {
      expect(screen.getByText('Active Conflicts')).toBeTruthy()
      expect(screen.getByText('Total Passes')).toBeTruthy()
    })
  })

  it('renders conflict card', async () => {
    render(<ConflictPanel />)
    await waitFor(() => {
      expect(screen.getByText(/Conflict at Jakarta/)).toBeTruthy()
    })
  })

  it('renders overlap badge', async () => {
    render(<ConflictPanel />)
    await waitFor(() => {
      const badge = document.querySelector('.overlap-badge')
      expect(badge).toBeTruthy()
      expect(badge.textContent).toContain('min overlap')
    })
  })

  it('renders pass details', async () => {
    render(<ConflictPanel />)
    await waitFor(() => {
      expect(screen.getByText('Pass 1')).toBeTruthy()
      expect(screen.getByText('Pass 2')).toBeTruthy()
    })
  })

  it('renders generate recommendation button', async () => {
    render(<ConflictPanel />)
    await waitFor(() => {
      expect(screen.getByText(/Generate AI Recommendation/)).toBeTruthy()
    })
  })

  it('calls generateRecommendation when button clicked', async () => {
    render(<ConflictPanel />)
    await waitFor(() => {
      expect(screen.getByText(/Generate AI Recommendation/)).toBeTruthy()
    })

    fireEvent.click(screen.getByText(/Generate AI Recommendation/))

    await waitFor(() => {
      expect(api.generateRecommendation).toHaveBeenCalled()
      expect(screen.getByText(/AI Recommendation/)).toBeTruthy()
    })
  })

  it('shows no conflicts when empty', async () => {
    api.getConflicts.mockResolvedValue({ conflicts: [] })

    render(<ConflictPanel />)
    await waitFor(() => {
      expect(screen.getByText('No Conflicts Detected')).toBeTruthy()
    })
  })

  it('shows error on API failure', async () => {
    api.getSatellites.mockRejectedValue(new Error('API Error'))

    render(<ConflictPanel />)
    await waitFor(() => {
      expect(screen.getByText(/Failed to load/)).toBeTruthy()
    })
  })

  it('renders filter controls', async () => {
    render(<ConflictPanel />)
    await waitFor(() => {
      expect(screen.getByText('Ground Station:')).toBeTruthy()
      expect(screen.getByText('Start Date:')).toBeTruthy()
      expect(screen.getByText('End Date:')).toBeTruthy()
    })
  })
})
