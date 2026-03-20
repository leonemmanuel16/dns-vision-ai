'use client'

import { DetectionEvent } from '@/hooks/useEvents'
import { EventCard } from './EventCard'

interface EventTimelineProps {
  events: DetectionEvent[]
}

export function EventTimeline({ events }: EventTimelineProps) {
  if (events.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-muted-foreground">
        No events found
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {events.map((event) => (
        <EventCard key={event.id} event={event} />
      ))}
    </div>
  )
}
