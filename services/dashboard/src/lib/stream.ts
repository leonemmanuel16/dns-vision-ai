export function sanitizeStreamName(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9_-]/g, '_')
    .replace(/^_+|_+$/g, '') || 'camera'
}

export function getGo2rtcBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_GO2RTC_URL
  if (envUrl && envUrl.trim()) return envUrl.trim()

  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol
    const hostname = window.location.hostname
    return `${protocol}//${hostname}:1984`
  }

  return 'http://localhost:1984'
}
