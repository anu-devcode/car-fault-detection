const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '')

async function request(path, options = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 60000)
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      signal: controller.signal,
    })
    const data = await response.json().catch(() => ({ detail: 'Invalid API response.' }))
    if (!response.ok) {
      const error = new Error(data.detail || `Request failed (${response.status}).`)
      error.response = { status: response.status, data }
      throw error
    }
    return data
  } catch (error) {
    if (error.name === 'AbortError') {
      const timeout = new Error('Request timeout.')
      timeout.code = 'ECONNABORTED'
      throw timeout
    }
    throw error
  } finally {
    clearTimeout(timer)
  }
}

export async function uploadAudio(file) {
  const body = new FormData()
  body.append('file', file)
  return request('/predict', { method: 'POST', body })
}

export const getClasses = () => request('/classes')
export const healthCheck = () => request('/')
