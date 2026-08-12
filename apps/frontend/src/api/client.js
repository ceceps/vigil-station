/**
 * API client for Mission Planning Assistant backend
 * Handles all HTTP requests to the FastAPI backend
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

/**
 * API methods
 */
export const api = {
  // Satellites
  getSatellites: async () => {
    const response = await apiClient.get('/satellites')
    return response.data
  },

  // Ground Stations
  getGroundStations: async () => {
    const response = await apiClient.get('/ground-stations')
    return response.data
  },

  // Passes
  getPasses: async (params = {}) => {
    const response = await apiClient.get('/passes', { params })
    return response.data
  },

  // Conflicts
  getConflicts: async (params = {}) => {
    const response = await apiClient.get('/conflicts', { params })
    return response.data
  },

  // Recommendations
  generateRecommendation: async (conflictId) => {
    const response = await apiClient.post('/recommendations', {
      conflict_id: conflictId,
    })
    return response.data
  },

  // Schedule Approval
  approveSchedule: async (scheduleId, approved, overrideReason = null) => {
    const response = await apiClient.post(`/schedule/${scheduleId}/approve`, {
      approved,
      override_reason: overrideReason,
    })
    return response.data
  },

  getScheduleStatus: async (scheduleId) => {
    const response = await apiClient.get(`/schedule/${scheduleId}/status`)
    return response.data
  },

  // Health check
  healthCheck: async () => {
    const response = await apiClient.get('/health')
    return response.data
  },

  // Space Weather (P1)
  getSpaceWeather: async (params = {}) => {
    const response = await apiClient.get('/space-weather', { params })
    return response.data
  },
}

export default api
