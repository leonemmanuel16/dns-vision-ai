'use client'

import { DetectionEvent } from '@/hooks/useEvents'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { formatDistanceToNow } from 'date-fns'

interface EventCardProps {
  event: DetectionEvent
}

const typeColors: Record<string, 'default' | 'success' | 'warning' | 'destructive'> = {
  person: 'default',
  vehicle: 'success',
  animal: 'warning',
  zone_crossing: 'destructive',
}

export function EventCard({ event }: EventCardProps) {
  return (
    <Card className="overflow-hidden">
      <div className="flex">
        {event.snapshot_url && (
          <div className="w-32 flex-shrink-0">
            <img
              src={event.snapshot_url}
              alt={event.label || event.event_type}
              className="h-full w-full object-cover"
            />
          </div>
        )}
        <CardContent className="flex flex-1 items-center justify-between p-4">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant={typeColors[event.event_type] || 'default'}>
                {event.event_type}
              </Badge>
              {event.label && (
                <span className="text-sm font-medium">{event.label}</span>
              )}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              {formatDistanceToNow(new Date(event.occurred_at), { addSuffix: true })}
            </p>
            {event.confidence && (
              <p className="text-xs text-muted-foreground">
                Confidence: {(event.confidence * 100).toFixed(1)}%
              </p>
            )}
          </div>
        </CardContent>
      </div>
    </Card>
  )
}
