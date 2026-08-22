import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import ScheduleTable from '../pages/ScheduleTable'
import ConflictPanel from '../pages/ConflictPanel'
import AnalyticsPanel from '../pages/AnalyticsPanel'
import api from '../api/client'

vi.mock('../api/client', () => ({
  default: {
    getSatellites: vi.fn(),
    getGroundStations: vi.fn(),
    getPasses: vi.fn(),
    getConflicts: vi.fn(),
    getAnalyticsInsights: vi.fn()
  }
}))

describe('Date Picker Max Restriction', () => {
  const today = new Date().toISOString().split('T')[0]

  beforeEach(() => {
    vi.clearAllMocks()
    api.getSatellites.mockResolvedValue({ satellites: [] })
    api.getGroundStations.mockResolvedValue({ ground_stations: [] })
    api.getPasses.mockResolvedValue({ passes: [] })
    api.getConflicts.mockResolvedValue({ conflicts: [] })
    api.getAnalyticsInsights.mockResolvedValue({
      summary: {},
      data_start_date: '2024-01-01',
      data_end_date: today
    })
  })

  it('disables dates after today in ScheduleTable date inputs', async () => {
    render(<ScheduleTable />)
    await waitFor(() => {
      const startInput = screen.getByLabelText ? screen.getByText('Start Date:').nextElementSibling : null
      const endInput = screen.getByText('End Date:').nextElementSibling
      expect(startInput.getAttribute('max')).toBe(today)
      expect(endInput.getAttribute('max')).toBe(today)
    })
  })

  it('disables dates after today in ConflictPanel date inputs', async () => {
    render(<ConflictPanel />)
    await waitFor(() => {
      const startInput = screen.getByText('Start Date:').nextElementSibling
      const endInput = screen.getByText('End Date:').nextElementSibling
      expect(startInput.getAttribute('max')).toBe(today)
      expect(endInput.getAttribute('max')).toBe(today)
    })
  })

  it('disables dates after today in AnalyticsPanel date inputs', async () => {
    render(<AnalyticsPanel />)
    await waitFor(() => {
      const startInput = screen.getByText('Start Date:').nextElementSibling
      const endInput = screen.getByText('End Date:').nextElementSibling
      expect(startInput.getAttribute('max')).toBe(today)
      expect(endInput.getAttribute('max')).toBe(today)
    })
  })
})
