import { describe, it, expect, vi, beforeEach } from 'vitest'
import api from '../api/client'

vi.mock('../api/client', () => ({
  default: {
    getSatellites: vi.fn(),
    getGroundStations: vi.fn(),
    getPasses: vi.fn(),
    getConflicts: vi.fn(),
    generateRecommendation: vi.fn(),
    approveSchedule: vi.fn(),
    getScheduleStatus: vi.fn(),
    healthCheck: vi.fn(),
    getSpaceWeather: vi.fn()
  }
}))

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getSatellites calls GET /satellites', async () => {
    const mockData = { satellites: [{ norad_id: 43569, name: 'IRIDIUM 160', group: 'iridium' }] }
    api.getSatellites.mockResolvedValue(mockData)
    const result = await api.getSatellites()
    expect(result).toEqual(mockData)
    expect(api.getSatellites).toHaveBeenCalledOnce()
  })

  it('getGroundStations calls GET /ground-stations', async () => {
    const mockData = { ground_stations: [{ id: 1, name: 'Jakarta', lat: -6.2088, lon: 106.8456 }] }
    api.getGroundStations.mockResolvedValue(mockData)
    const result = await api.getGroundStations()
    expect(result).toEqual(mockData)
  })

  it('getPasses calls GET /passes with params', async () => {
    const mockData = { passes: [{ id: 'pass_1', satellite_id: 43569 }] }
    api.getPasses.mockResolvedValue(mockData)
    const result = await api.getPasses({ start: '2024-01-01T00:00:00Z' })
    expect(result).toEqual(mockData)
  })

  it('getConflicts calls GET /conflicts', async () => {
    const mockData = { conflicts: [] }
    api.getConflicts.mockResolvedValue(mockData)
    const result = await api.getConflicts()
    expect(result).toEqual(mockData)
  })

  it('generateRecommendation calls POST /recommendations', async () => {
    const mockData = { recommendation: { suggested_action: 'reschedule', reasoning: 'Test' } }
    api.generateRecommendation.mockResolvedValue(mockData)
    const result = await api.generateRecommendation('conflict_1_2')
    expect(result).toEqual(mockData)
  })

  it('approveSchedule calls POST /schedule/:id/approve', async () => {
    const mockData = { status: 'approved', schedule_id: 'pass_1' }
    api.approveSchedule.mockResolvedValue(mockData)
    const result = await api.approveSchedule('pass_1', true)
    expect(result).toEqual(mockData)
  })

  it('approveSchedule with override reason', async () => {
    const mockData = { status: 'rejected', schedule_id: 'pass_1' }
    api.approveSchedule.mockResolvedValue(mockData)
    const result = await api.approveSchedule('pass_1', false, 'Weather concern')
    expect(result).toEqual(mockData)
  })

  it('healthCheck calls GET /health', async () => {
    const mockData = { status: 'healthy' }
    api.healthCheck.mockResolvedValue(mockData)
    const result = await api.healthCheck()
    expect(result).toEqual(mockData)
  })

  it('getSpaceWeather calls GET /space-weather', async () => {
    const mockData = { events: [], overall_status: 'quiet' }
    api.getSpaceWeather.mockResolvedValue(mockData)
    const result = await api.getSpaceWeather()
    expect(result).toEqual(mockData)
  })
})
