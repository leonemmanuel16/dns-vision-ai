'use client'

import { useState, useEffect, useCallback } from 'react'
import { apiFetch } from '@/lib/api'

export interface Camera {
  id: string
  name: string
  ip_address: string
  onvif_port: number
  manufacturer: string | null
  model: string | null
  has_ptz: boolean
  location: string | null
  is_enabled: boolean
  is_online: boolean
  last_seen_at: string | null
  created_at: string
}

export function useCameras() {
  const [cameras, setCameras] = useState<Camera[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCameras = useCallback(async () => {
    try {
      setLoading(true)
      const data = await apiFetch<{ cameras: Camera[]; total: number }>('/api/cameras')
      setCameras(data.cameras)
      setError(null)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCameras()
  }, [fetchCameras])

  return { cameras, loading, error, refresh: fetchCameras }
}
