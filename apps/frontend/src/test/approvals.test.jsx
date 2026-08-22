import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import Approvals from '../pages/Approvals'
import api from '../api/client'

vi.mock('../api/client', () => ({
  default: {
    getSatellites: vi.fn(),
    getGroundStations: vi.fn(),
    getConflicts: vi.fn(),
    getPasses: vi.fn(),
    generateRecommendation: vi.fn(),
    approveSchedule: vi.fn(),
    getAnalyticsInsights: vi.fn()
  }
}))

describe('Approvals', () => {
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
    api.getAnalyticsInsights.mockResolvedValue({ recommendations_history: [], schedules_history: [] })
    api.generateRecommendation.mockResolvedValue({
      recommendation: { suggested_action: 'reschedule', target_pass_id: 'pass_1', reasoning: 'Test reasoning' }
    })
    api.approveSchedule.mockResolvedValue({ status: 'approved' })
  })

  it('renders header', async () => {
    render(<Approvals />)
    await waitFor(() => {
      expect(screen.getByText(/Approval Dashboard/)).toBeTruthy()
    })
  })

  it('renders stat cards', async () => {
    render(<Approvals />)
    await waitFor(() => {
      expect(screen.getByText('Pending Approvals')).toBeTruthy()
      expect(screen.getByText('Approved')).toBeTruthy()
      expect(screen.getByText('Overridden')).toBeTruthy()
    })
  })

  it('renders approval card', async () => {
    render(<Approvals />)
    await waitFor(() => {
      expect(screen.getByText(/Conflict at Jakarta/)).toBeTruthy()
    })
  })

  it('renders generate recommendation button', async () => {
    render(<Approvals />)
    await waitFor(() => {
      expect(screen.getByText(/Generate Recommendation First/)).toBeTruthy()
    })
  })

  it('shows approve/override after recommendation', async () => {
    render(<Approvals />)
    await waitFor(() => {
      expect(screen.getByText(/Generate Recommendation First/)).toBeTruthy()
    })

    fireEvent.click(screen.getByText(/Generate Recommendation First/))

    await waitFor(() => {
      expect(screen.getByText(/Approve Recommendation/)).toBeTruthy()
      expect(screen.getByText(/Override/)).toBeTruthy()
    })
  })

  it('calls approveSchedule on approve click', async () => {
    render(<Approvals />)
    await waitFor(() => {
      expect(screen.getByText(/Generate Recommendation First/)).toBeTruthy()
    })

    fireEvent.click(screen.getByText(/Generate Recommendation First/))

    await waitFor(() => {
      expect(screen.getByText(/Approve Recommendation/)).toBeTruthy()
    })

    fireEvent.click(screen.getByText(/Approve Recommendation/))

    await waitFor(() => {
      expect(api.approveSchedule).toHaveBeenCalledWith('pass_1', true)
    })
  })

  it('shows no pending approvals when empty', async () => {
    api.getConflicts.mockResolvedValue({ conflicts: [] })

    render(<Approvals />)
    await waitFor(() => {
      expect(screen.getByText('No Approvals in Selected Filter')).toBeTruthy()
    })
  })

  it('shows error on API failure', async () => {
    api.getSatellites.mockRejectedValue(new Error('API Error'))

    render(<Approvals />)
    await waitFor(() => {
      expect(screen.getByText(/Failed to load approval data/)).toBeTruthy()
    })
  })

  it('renders refresh button', async () => {
    render(<Approvals />)
    await waitFor(() => {
      expect(screen.getByText(/Refresh/)).toBeTruthy()
    })
  })

  it('reloads data on refresh click', async () => {
    render(<Approvals />)
    await waitFor(() => {
      expect(api.getConflicts).toHaveBeenCalledTimes(1)
    })

    fireEvent.click(screen.getByText(/Refresh/))

    await waitFor(() => {
      expect(api.getConflicts.mock.calls.length).toBeGreaterThanOrEqual(2)
    })
  })
})
