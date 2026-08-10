import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import ScheduleTable from '../pages/ScheduleTable'
import api from '../api/client'

vi.mock('../api/client', () => ({
  default: {
    getSatellites: vi.fn(),
    getGroundStations: vi.fn(),
    getPasses: vi.fn()
  }
}))

describe('ScheduleTable', () => {
  const mockSatellites = {
    satellites: [{ norad_id: 43569, name: 'IRIDIUM 160', group: 'iridium' }]
  }

  const mockGroundStations = {
    ground_stations: [{ id: 1, name: 'Jakarta', lat: -6.2088, lon: 106.8456, min_elevation_deg: 10 }]
  }

  const mockPasses = {
    passes: [{
      id: 'pass_1',
      satellite_id: 43569,
      ground_station_id: 1,
      start_time: '2024-01-01T10:00:00Z',
      end_time: '2024-01-01T10:10:00Z',
      max_elevation_deg: 45.5
    }]
  }

  beforeEach(() => {
    vi.clearAllMocks()
    api.getSatellites.mockResolvedValue(mockSatellites)
    api.getGroundStations.mockResolvedValue(mockGroundStations)
    api.getPasses.mockResolvedValue(mockPasses)
  })

  it('renders loading shimmer initially', () => {
    render(<ScheduleTable />)
    expect(document.querySelector('.shimmer-stats')).toBeTruthy()
  })

  it('renders header after loading', async () => {
    render(<ScheduleTable />)
    await waitFor(() => {
      expect(screen.getByText(/Satellite Pass Schedule/)).toBeTruthy()
    })
  })

  it('renders stat cards after loading', async () => {
    render(<ScheduleTable />)
    await waitFor(() => {
      expect(screen.getByText('Total Passes')).toBeTruthy()
      expect(screen.getByText('Satellites')).toBeTruthy()
      expect(screen.getByText('Ground Stations')).toBeTruthy()
    })
  })

  it('renders pass data in table', async () => {
    render(<ScheduleTable />)
    await waitFor(() => {
      expect(screen.getAllByText('IRIDIUM 160').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('Jakarta').length).toBeGreaterThanOrEqual(1)
    })
  })

  it('renders filter controls', async () => {
    render(<ScheduleTable />)
    await waitFor(() => {
      expect(screen.getByText('Satellite:')).toBeTruthy()
      expect(screen.getByText('Ground Station:')).toBeTruthy()
      expect(screen.getByText('Start Date:')).toBeTruthy()
      expect(screen.getByText('End Date:')).toBeTruthy()
    })
  })

  it('renders refresh button', async () => {
    render(<ScheduleTable />)
    await waitFor(() => {
      expect(screen.getByText(/Refresh/)).toBeTruthy()
    })
  })

  it('calls getPasses when refresh is clicked', async () => {
    render(<ScheduleTable />)
    await waitFor(() => {
      expect(api.getPasses).toHaveBeenCalled()
    })

    fireEvent.click(screen.getByText(/Refresh/))

    await waitFor(() => {
      expect(api.getPasses.mock.calls.length).toBeGreaterThanOrEqual(2)
    })
  })

  it('shows error state on API failure', async () => {
    api.getSatellites.mockRejectedValue(new Error('API Error'))

    render(<ScheduleTable />)
    await waitFor(() => {
      expect(screen.getByText(/Failed to load/)).toBeTruthy()
    })
  })

  it('renders elevation badge', async () => {
    render(<ScheduleTable />)
    await waitFor(() => {
      const badge = document.querySelector('.elevation-badge')
      expect(badge).toBeTruthy()
      expect(badge.textContent).toContain('45.5')
    })
  })
})
