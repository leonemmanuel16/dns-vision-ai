'use client'

import { useState, useEffect, useCallback } from 'react'
import { apiFetch } from '@/lib/api'

export interface DetectionEvent {
  id: string
  camera_id: string
  event_type: string
  label: string | null
  confidence: number | null
  bbox: Record<string, number> | null
  zone_id: string | null
  snapshot_url: string | null
  clip_url: string | null
  thumbnail_url: string | null
  metadata: Record<string, any> | null
  occurred_at: string
  created_at: string
}

interface UseEventsOptions {
  camera_id?: string
  event_type?: string
  limit?: number
}

export function useEvents(options: UseEventsOptions = {}) {
  const [events, setEvents] = useState<DetectionEvent[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchEvents = useCallback(async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (options.camera_id) params.set('camera_id', options.camera_id)
      if (options.event_type) params.set('event_type', options.event_type)
      if (options.limit) params.set('limit', String(options.limit))

      const data = await apiFetch<{ events: DetectionEvent[]; total: number }>(
        `/api/events?${params.toString()}`
      )
      setEvents(data.events)
      setTotal(data.total)
      setError(null)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [options.camera_id, options.event_type, options.limit])

  useEffect(() => {
    fetchEvents()
  }, [fetchEvents])

  return { events, total, loading, error, refresh: fetchEvents }
}
