import { config } from '../config'

/**
 * Centralized API client that handles all HTTP communication between the frontend and backend services.
 *
 * Creates an Axios instance with base configuration
 * Automatically attaches JWT tokens to requests
 * Provides methods for authentication endpoints
 * Handles automatic token refresh on 401 errors
 */
class ApiClient {
  constructor() {
    this.baseUrl = config.apiBaseUrl
    this.refreshTokenKey = 'refresh_token'
    this.isRefreshing = false
    this.refreshPromise = null
  }

  getRefreshToken() {
    return localStorage.getItem(this.refreshTokenKey)
  }

  setRefreshToken(token) {
    if (token) {
      localStorage.setItem(this.refreshTokenKey, token)
    } else {
      localStorage.removeItem(this.refreshTokenKey)
    }
  }

  async refreshAccessToken() {
    const refreshToken = this.getRefreshToken()
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    const response = await fetch(`${this.baseUrl}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
      credentials: 'include',
    })

    if (!response.ok) {
      this.setRefreshToken(null) // Clear invalid refresh token
      throw new Error('Failed to refresh token')
    }

    const data = await response.json()
    // Backend returns new access_token in cookie, and same refresh_token
    return data
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

      // Handle 401 Unauthorized - try to refresh token
      if (response.status === 401) {
        const currentPath = window.location.pathname
        const isAuthCheck = endpoint === '/auth/me'
        const isOnAuthPage = currentPath === '/login'
        const isRefreshEndpoint = endpoint === '/auth/refresh'

        // Don't try to refresh if we're already refreshing or on auth pages
        if (!isRefreshEndpoint && !isOnAuthPage && this.getRefreshToken()) {
          // Try to refresh the token
          if (!this.isRefreshing) {
            this.isRefreshing = true
            this.refreshPromise = this.refreshAccessToken()
              .finally(() => {
                this.isRefreshing = false
                this.refreshPromise = null
              })
          }

          try {
            await this.refreshPromise
            // Retry the original request with new access token
            const retryResponse = await fetch(url, config)
            const retryData = await retryResponse.json().catch(() => ({}))

            if (!retryResponse.ok) {
              throw new Error(retryData.message || `HTTP ${retryResponse.status}`)
            }

            return retryData
          } catch (refreshError) {
            console.error('Token refresh failed:', refreshError)
            // Refresh failed, redirect to login
            if (!isAuthCheck) {
              window.location.href = '/login'
            }
            throw new Error('Unauthorized')
          }
        } else {
          // No refresh token or already on auth page
          if (!isAuthCheck && !isOnAuthPage) {
            window.location.href = '/login'
          }
          throw new Error('Unauthorized')
        }
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

    // Store refresh token for auto-refresh
    if (data.refresh_token) {
      this.setRefreshToken(data.refresh_token)
    }

    return data
  }

  async logout() {
    const refreshToken = this.getRefreshToken()

    try {
      await this.request('/auth/logout', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      // Clear refresh token from localStorage regardless of API call result
      this.setRefreshToken(null)
    }
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

  async revokeUserSessions(userId) {
    return this.request(`/auth/users/${userId}/revoke-sessions`, {
      method: 'POST',
    })
  }
}

export const api = new ApiClient()
