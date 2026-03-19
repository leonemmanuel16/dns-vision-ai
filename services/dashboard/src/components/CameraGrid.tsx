'use client'

import Link from 'next/link'
import { Camera } from '@/hooks/useCameras'
import { VideoPlayer } from './VideoPlayer'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface CameraGridProps {
  cameras: Camera[]
  columns?: 2 | 3 | 4
}

export function CameraGrid({ cameras, columns = 3 }: CameraGridProps) {
  const gridClass = {
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
  }

  return (
    <div className={cn('grid gap-4', gridClass[columns])}>
      {cameras.map((camera) => (
        <Link
          key={camera.id}
          href={`/dashboard/cameras/${camera.id}`}
          className="group relative overflow-hidden rounded-lg border bg-card transition-colors hover:border-primary"
        >
          <div className="relative aspect-video bg-black">
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
          <div className="flex items-center justify-between p-3">
            <div>
              <p className="font-medium">{camera.name}</p>
              <p className="text-xs text-muted-foreground">{camera.location || camera.ip_address}</p>
            </div>
            <Badge variant={camera.is_online ? 'success' : 'destructive'}>
              {camera.is_online ? 'Online' : 'Offline'}
            </Badge>
          </div>
        </Link>
      ))}
    </div>
  )
}
