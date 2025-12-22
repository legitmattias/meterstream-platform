import { config } from '../config'

/**
 * Centralized API client that handles all HTTP communication between the frontend and backend services.
 * 
 * Creates an Axios instance with base configuration
 * Automatically attaches JWT tokens to requests
 * Provides methods for authentication endpoints
 */
class ApiClient {
  constructor() {
    this.baseUrl = config.apiBaseUrl
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    const config = {
      ...options,
      headers,
      credentials: 'include',  // Send cookies with requests (JWT in HttpOnly cookie)
    }

    try {
      const response = await fetch(url, config)

      // Handle 401 Unauthorized
      if (response.status === 401) {
        window.location.href = '/login'
        throw new Error('Unauthorized')
      }

      // Parse JSON response
      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(data.message || `HTTP ${response.status}`)
      }

      return data
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  // Auth endpoints
  // NOTE: Endpoints should NOT include /api prefix - it's added via baseUrl
  async login(email, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  }

  async register(email, password, name) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    })
  }

  // Health check
  async health() {
    return this.request('/health')
  }
}

export const api = new ApiClient()
