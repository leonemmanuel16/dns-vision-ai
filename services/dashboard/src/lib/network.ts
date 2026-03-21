export function getApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL
  if (envUrl && envUrl.trim()) return envUrl.trim()

  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol
    const hostname = window.location.hostname
    return `${protocol}//${hostname}:8000`
  }

  return 'http://localhost:8000'
}

export function getWsBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_WS_URL
  if (envUrl && envUrl.trim()) return envUrl.trim()

  if (typeof window !== 'undefined') {
    const isHttps = window.location.protocol === 'https:'
    const wsProto = isHttps ? 'wss' : 'ws'
    const hostname = window.location.hostname
    return `${wsProto}://${hostname}:8000/ws`
  }

  return 'ws://localhost:8000/ws'
}
