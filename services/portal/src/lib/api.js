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
      // Don't redirect if we're already on /login or /register, or if it's /auth/me checking session
      if (response.status === 401) {
        const currentPath = window.location.pathname
        const isAuthCheck = endpoint === '/auth/me'
        const isOnAuthPage = currentPath === '/login' || currentPath === '/register'

        if (!isAuthCheck && !isOnAuthPage) {
          window.location.href = '/login'
        }
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

  // Admin user management endpoints
  async getUsers(page = 1, pageSize = 20, search = '', role = '') {
    let url = `/auth/users?page=${page}&page_size=${pageSize}`
    if (search) url += `&search=${encodeURIComponent(search)}`
    if (role) url += `&role=${encodeURIComponent(role)}`
    return this.request(url)
  }

  async createUser(userData) {
    return this.request('/auth/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    })
  }

  async updateUser(userId, updateData) {
    return this.request(`/auth/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    })
  }

  async deleteUser(userId) {
    return this.request(`/auth/users/${userId}`, {
      method: 'DELETE',
    })
  }
}

export const api = new ApiClient()
