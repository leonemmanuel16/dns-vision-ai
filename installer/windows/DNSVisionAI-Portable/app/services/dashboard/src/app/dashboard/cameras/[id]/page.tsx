'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { apiFetch } from '@/lib/api'
import { Camera } from '@/hooks/useCameras'
import { VideoPlayer } from '@/components/VideoPlayer'
import { PTZControls } from '@/components/PTZControls'
import { EventTimeline } from '@/components/EventTimeline'
import { useEvents } from '@/hooks/useEvents'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { ArrowLeft, Trash2 } from 'lucide-react'

export default function CameraDetailPage() {
  const params = useParams()
  const router = useRouter()
  const cameraId = params.id as string
  const [camera, setCamera] = useState<Camera | null>(null)
  const [loading, setLoading] = useState(true)
  const { events } = useEvents({ camera_id: cameraId, limit: 20 })

  useEffect(() => {
    async function fetchCamera() {
      try {
        const data = await apiFetch<Camera>(`/api/cameras/${cameraId}`)
        setCamera(data)
      } catch (e) {
        console.error('Failed to load camera:', e)
      } finally {
        setLoading(false)
      }
    }
    fetchCamera()
  }, [cameraId])

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this camera?')) return
    try {
      await apiFetch(`/api/cameras/${cameraId}`, { method: 'DELETE' })
      router.push('/dashboard/cameras')
    } catch (e) {
      console.error('Failed to delete camera:', e)
    }
  }

  if (loading) return <div className="animate-pulse text-muted-foreground">Loading...</div>
  if (!camera) return <div className="text-muted-foreground">Camera not found</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push('/dashboard/cameras')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h2 className="text-2xl font-bold">{camera.name}</h2>
            <p className="text-sm text-muted-foreground">{camera.location || camera.ip_address}</p>
          </div>
          <Badge variant={camera.is_online ? 'success' : 'destructive'}>
            {camera.is_online ? 'Online' : 'Offline'}
          </Badge>
        </div>
        <Button variant="destructive" size="sm" onClick={handleDelete}>
          <Trash2 className="mr-2 h-4 w-4" /> Delete
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="relative aspect-video overflow-hidden rounded-lg border bg-black">
            {camera.is_online ? (
              <VideoPlayer
                cameraName={camera.name.replace(/\s+/g, '_').toLowerCase()}
                className="absolute inset-0"
              />
            ) : (
              <div className="flex h-full items-center justify-center text-muted-foreground">
                Camera Offline
              </div>
            )}
          </div>
        </div>

        <div className="space-y-4">
          {camera.has_ptz && <PTZControls cameraId={camera.id} />}

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Camera Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">IP</span>
                <span>{camera.ip_address}:{camera.onvif_port}</span>
              </div>
              {camera.manufacturer && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Manufacturer</span>
                  <span>{camera.manufacturer}</span>
                </div>
              )}
              {camera.model && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Model</span>
                  <span>{camera.model}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">PTZ</span>
                <span>{camera.has_ptz ? 'Yes' : 'No'}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Events</CardTitle>
        </CardHeader>
        <CardContent>
          <EventTimeline events={events} />
        </CardContent>
      </Card>
    </div>
  )
}
