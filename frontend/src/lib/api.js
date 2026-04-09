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
