'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { apiFetch } from '@/lib/api'
import { DetectionEvent } from '@/hooks/useEvents'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { ArrowLeft } from 'lucide-react'
import { format } from 'date-fns'

export default function EventDetailPage() {
  const params = useParams()
  const router = useRouter()
  const eventId = params.id as string
  const [event, setEvent] = useState<DetectionEvent | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchEvent() {
      try {
        const data = await apiFetch<DetectionEvent>(`/api/events/${eventId}`)
        setEvent(data)
      } catch (e) {
        console.error('Failed to load event:', e)
      } finally {
        setLoading(false)
      }
    }
    fetchEvent()
  }, [eventId])

  if (loading) return <div className="animate-pulse text-muted-foreground">Loading...</div>
  if (!event) return <div className="text-muted-foreground">Event not found</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push('/dashboard/events')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h2 className="text-2xl font-bold">Event Detail</h2>
        <Badge>{event.event_type}</Badge>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {event.snapshot_url && (
          <div className="overflow-hidden rounded-lg border">
            <img src={event.snapshot_url} alt="Event snapshot" className="w-full" />
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Type</span>
              <span className="capitalize">{event.event_type}</span>
            </div>
            {event.label && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Label</span>
                <span>{event.label}</span>
              </div>
            )}
            {event.confidence && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Confidence</span>
                <span>{(event.confidence * 100).toFixed(1)}%</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-muted-foreground">Time</span>
              <span>{format(new Date(event.occurred_at), 'PPpp')}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Camera</span>
              <span className="font-mono text-xs">{event.camera_id}</span>
            </div>
            {event.bbox && (
              <div>
                <span className="text-muted-foreground">Bounding Box</span>
                <pre className="mt-1 rounded bg-secondary p-2 text-xs">
                  {JSON.stringify(event.bbox, null, 2)}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {event.clip_url && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Video Clip</CardTitle>
          </CardHeader>
          <CardContent>
            <video src={event.clip_url} controls className="w-full rounded-lg" />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
