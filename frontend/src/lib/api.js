const rawBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').trim()

const normalizedBaseUrl = rawBaseUrl.endsWith('/')
  ? rawBaseUrl.slice(0, -1)
  : rawBaseUrl

export function apiUrl(path) {
  if (!normalizedBaseUrl) {
    return path
  }

  return `${normalizedBaseUrl}${path}`
}

export async function apiRequest(path, options = {}, token = '') {
  const headers = new Headers(options.headers || {})
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(apiUrl(path), {
    ...options,
    headers,
  })

  const isJson = response.headers.get('content-type')?.includes('application/json')
  const data = isJson ? await response.json() : null

  if (!response.ok) {
    const detail = data?.detail || 'Request failed.'
    throw new Error(detail)
  }

  return data
}
