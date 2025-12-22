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
    this.token = null
  }

  setToken(token) {
    this.token = token
  }

  getToken() {
    return this.token
  }

  clearToken() {
    this.token = null
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const config = {
      ...options,
      headers,
    }

    try {
      const response = await fetch(url, config)

      // Handle 401 Unauthorized
      if (response.status === 401) {
        this.clearToken()
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
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    if (data.access_token) {
      this.setToken(data.access_token)
    }
    return data
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
