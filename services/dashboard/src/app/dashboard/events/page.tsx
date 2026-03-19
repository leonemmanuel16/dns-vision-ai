'use client'

import { useState } from 'react'
import { useEvents } from '@/hooks/useEvents'
import { useCameras } from '@/hooks/useCameras'
import { EventTimeline } from '@/components/EventTimeline'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'

export default function EventsPage() {
  const [cameraFilter, setCameraFilter] = useState<string>('')
  const [typeFilter, setTypeFilter] = useState<string>('')
  const { events, total, loading, refresh } = useEvents({
    camera_id: cameraFilter || undefined,
    event_type: typeFilter || undefined,
    limit: 50,
  })
  const { cameras } = useCameras()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold">Events</h2>
        <Button variant="outline" size="sm" onClick={refresh}>
          <RefreshCw className="mr-2 h-4 w-4" /> Refresh
        </Button>
      </div>

      <div className="flex flex-wrap gap-3">
        <select
          className="rounded-md border bg-background px-3 py-2 text-sm"
          value={cameraFilter}
          onChange={(e) => setCameraFilter(e.target.value)}
        >
          <option value="">All Cameras</option>
          {cameras.map((cam) => (
            <option key={cam.id} value={cam.id}>{cam.name}</option>
          ))}
        </select>

        <select
          className="rounded-md border bg-background px-3 py-2 text-sm"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">All Types</option>
          <option value="person">Person</option>
          <option value="vehicle">Vehicle</option>
          <option value="animal">Animal</option>
          <option value="zone_crossing">Zone Crossing</option>
        </select>

        <span className="flex items-center text-sm text-muted-foreground">
          {total} events found
        </span>
      </div>

      {loading ? (
        <div className="animate-pulse text-muted-foreground">Loading events...</div>
      ) : (
        <EventTimeline events={events} />
      )}
    </div>
  )
}
