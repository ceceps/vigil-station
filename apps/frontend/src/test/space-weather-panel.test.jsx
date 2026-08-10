import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import SpaceWeatherPanel from '../pages/SpaceWeatherPanel'
import api from '../api/client'

vi.mock('../api/client', () => ({
  default: {
    getSpaceWeather: vi.fn()
  }
}))

describe('SpaceWeatherPanel', () => {
  const mockQuiet = {
    events: [],
    overall_status: 'quiet',
    communication_impact: { affected: false, recommendation: 'Conditions are favorable' }
  }

  const mockActive = {
    events: [{
      event_type: 'solar_flare',
      severity: 'moderate',
      start_time: '2024-01-01T10:00:00Z',
      end_time: '2024-01-01T11:00:00Z',
      description: 'M-class solar flare detected',
      source_location: 'AR12345'
    }],
    overall_status: 'disturbed',
    communication_impact: {
      affected: true,
      recommendation: 'Consider delaying operations',
      risk_factors: ['Signal degradation', 'Increased bit error rate']
    }
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders header', async () => {
    api.getSpaceWeather.mockResolvedValue(mockQuiet)
    render(<SpaceWeatherPanel />)
    await waitFor(() => {
      expect(screen.getByText(/Space Weather Conditions/)).toBeTruthy()
    })
  })

  it('shows loading shimmer initially', () => {
    api.getSpaceWeather.mockReturnValue(new Promise(() => {}))
    render(<SpaceWeatherPanel />)
    expect(document.querySelector('.shimmer-stats')).toBeTruthy()
  })

  it('renders stat cards', async () => {
    api.getSpaceWeather.mockResolvedValue(mockQuiet)
    render(<SpaceWeatherPanel />)
    await waitFor(() => {
      expect(screen.getByText('Overall Status')).toBeTruthy()
      expect(screen.getByText('Active Events')).toBeTruthy()
      expect(screen.getByText('Communication Impact')).toBeTruthy()
    })
  })

  it('shows quiet status', async () => {
    api.getSpaceWeather.mockResolvedValue(mockQuiet)
    render(<SpaceWeatherPanel />)
    await waitFor(() => {
      expect(screen.getByText('QUIET')).toBeTruthy()
    })
  })

  it('shows no communication impact', async () => {
    api.getSpaceWeather.mockResolvedValue(mockQuiet)
    render(<SpaceWeatherPanel />)
    await waitFor(() => {
      expect(screen.getByText('NO')).toBeTruthy()
    })
  })

  it('shows recommendation', async () => {
    api.getSpaceWeather.mockResolvedValue(mockQuiet)
    render(<SpaceWeatherPanel />)
    await waitFor(() => {
      expect(screen.getByText('Conditions are favorable')).toBeTruthy()
    })
  })

  it('shows no events message', async () => {
    api.getSpaceWeather.mockResolvedValue(mockQuiet)
    render(<SpaceWeatherPanel />)
    await waitFor(() => {
      expect(screen.getByText('No Active Space Weather Events')).toBeTruthy()
    })
  })

  it('renders active events', async () => {
    api.getSpaceWeather.mockResolvedValue(mockActive)
    render(<SpaceWeatherPanel />)
    await waitFor(() => {
      expect(screen.getByText('SOLAR FLARE')).toBeTruthy()
      expect(screen.getByText('M-class solar flare detected')).toBeTruthy()
    })
  })

  it('shows disturbed status for active events', async () => {
    api.getSpaceWeather.mockResolvedValue(mockActive)
    render(<SpaceWeatherPanel />)
    await waitFor(() => {
      expect(screen.getByText('DISTURBED')).toBeTruthy()
      expect(screen.getByText('YES')).toBeTruthy()
    })
  })

  it('renders risk factors', async () => {
    api.getSpaceWeather.mockResolvedValue(mockActive)
    render(<SpaceWeatherPanel />)
    await waitFor(() => {
      expect(screen.getByText(/Risk Factors/)).toBeTruthy()
      expect(screen.getByText('Signal degradation')).toBeTruthy()
      expect(screen.getByText('Increased bit error rate')).toBeTruthy()
    })
  })

  it('renders refresh button', async () => {
    api.getSpaceWeather.mockResolvedValue(mockQuiet)
    render(<SpaceWeatherPanel />)
    await waitFor(() => {
      expect(screen.getByText(/Refresh/)).toBeTruthy()
    })
  })

  it('shows error on API failure', async () => {
    api.getSpaceWeather.mockRejectedValue(new Error('API Error'))
    render(<SpaceWeatherPanel />)
    await waitFor(() => {
      expect(screen.getByText(/Failed to load space weather data/)).toBeTruthy()
    })
  })

  it('calls getSpaceWeather when refresh clicked', async () => {
    api.getSpaceWeather.mockResolvedValue(mockQuiet)
    render(<SpaceWeatherPanel />)
    await waitFor(() => {
      expect(api.getSpaceWeather).toHaveBeenCalledTimes(1)
    })

    fireEvent.click(screen.getByText(/Refresh/))

    await waitFor(() => {
      expect(api.getSpaceWeather.mock.calls.length).toBeGreaterThanOrEqual(2)
    })
  })
})
