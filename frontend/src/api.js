/**
 * HVCS API client
 *
 * Wraps every fetch call with:
 *   - Base URL prefix (/api/v1)
 *   - Authorization: Bearer <access_token> header from localStorage
 *   - Automatic 401 → redirect to login
 */

const BASE = '/api/v1'

function getToken() {
  return localStorage.getItem('access')
}

function saveTokens({ access, refresh }) {
  localStorage.setItem('access', access)
  localStorage.setItem('refresh', refresh)
}

function clearTokens() {
  localStorage.removeItem('access')
  localStorage.removeItem('refresh')
}

async function request(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers })

  if (res.status === 401) {
    clearTokens()
    if (!window.location.pathname.endsWith('/login')) {
      window.location.href = '/react/login'
    }
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw err
  }

  if (res.status === 204) return null
  return res.json()
}

// Auth
export const login = (username, password) =>
  request('/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  }).then(data => { saveTokens(data); return data })

export const logout = () => clearTokens()

export const getMe = () => request('/auth/me/')

export const register = (data) =>
  request('/auth/register/', { method: 'POST', body: JSON.stringify(data) })

// Dashboards
export const getAdminDashboard    = () => request('/dashboard/admin/')
export const getManagerDashboard  = () => request('/dashboard/manager/')
export const getCaregiverDashboard = () => request('/dashboard/caregiver/')

// Clients
export const getClients    = () => request('/clients/')
export const getClient     = (id) => request(`/clients/${id}/`)
export const createClient  = (data) => request('/clients/', { method: 'POST', body: JSON.stringify(data) })
export const updateClient  = (id, data) => request(`/clients/${id}/`, { method: 'PATCH', body: JSON.stringify(data) })
export const deleteClient  = (id) => request(`/clients/${id}/`, { method: 'DELETE' })

// Caregivers
export const getCaregivers   = () => request('/caregivers/')
export const getCaregiver    = (id) => request(`/caregivers/${id}/`)
export const createCaregiver = (data) => request('/caregivers/', { method: 'POST', body: JSON.stringify(data) })
export const updateCaregiver = (id, data) => request(`/caregivers/${id}/`, { method: 'PATCH', body: JSON.stringify(data) })
export const deleteCaregiver = (id) => request(`/caregivers/${id}/`, { method: 'DELETE' })

// Visits
export const getVisits   = (params = {}) => request('/visits/?' + new URLSearchParams(params))
export const getVisit    = (id) => request(`/visits/${id}/`)
export const createVisit = (data) => request('/visits/', { method: 'POST', body: JSON.stringify(data) })
export const updateVisit = (id, data) => request(`/visits/${id}/`, { method: 'PATCH', body: JSON.stringify(data) })
export const deleteVisit = (id) => request(`/visits/${id}/`, { method: 'DELETE' })
export const checkinVisit  = (id, coords) => request(`/visits/${id}/checkin/`,  { method: 'POST', body: JSON.stringify(coords) })
export const checkoutVisit = (id) => request(`/visits/${id}/checkout/`, { method: 'POST', body: '{}' })

// Managers
export const getManagers   = () => request('/managers/')
export const createManager = (data) => request('/managers/', { method: 'POST', body: JSON.stringify(data) })
export const updateManager = (id, data) => request(`/managers/${id}/`, { method: 'PATCH', body: JSON.stringify(data) })
export const deleteManager = (id) => request(`/managers/${id}/`, { method: 'DELETE' })

// Compliance
export const getCompliance = (params = {}) => request('/compliance/?' + new URLSearchParams(params))
