export class ApiError extends Error {
  constructor(message, status, details) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

function normalizeBaseUrl(value) {
  const path = (value || '').trim().replace(/^\/+|\/+$/g, '').replace(/\/{2,}/g, '/') || 'api/v1'
  return `/${path}`
}

const API_BASE_URL = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL)

function apiUrl(path) {
  // Django endpoints require their declared trailing slash for POST requests;
  // strip only leading separators while joining the configured API prefix.
  const endpoint = String(path).replace(/^\/+/, '').replace(/\/{2,}/g, '/')
  return `${API_BASE_URL}/${endpoint}`
}

function csrfToken() {
  const cookie = document.cookie.split('; ').find((part) => part.startsWith('csrftoken='))
  return cookie ? decodeURIComponent(cookie.slice('csrftoken='.length)) : null
}

export async function apiRequest(path, { method = 'GET', body, signal } = {}) {
  const headers = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (method !== 'GET' && method !== 'HEAD') {
    const token = csrfToken()
    if (token) headers['X-CSRFToken'] = token
  }

  const response = await fetch(apiUrl(path), {
    method,
    credentials: 'same-origin',
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(data?.message || `خطای درخواست (${response.status})`, response.status, data)
  }
  return data
}
