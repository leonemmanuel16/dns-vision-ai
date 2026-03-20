'use client'

import { Button } from '@/components/ui/button'
import { apiFetch } from '@/lib/api'
import {
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ZoomIn,
  ZoomOut,
  Square,
} from 'lucide-react'

interface PTZControlsProps {
  cameraId: string
}

export function PTZControls({ cameraId }: PTZControlsProps) {
  const sendPTZ = async (pan: number, tilt: number, zoom: number) => {
    await apiFetch(`/api/cameras/${cameraId}/ptz`, {
      method: 'POST',
      body: JSON.stringify({ action: 'move', pan, tilt, zoom }),
    })
  }

  const stopPTZ = async () => {
    await apiFetch(`/api/cameras/${cameraId}/ptz`, {
      method: 'POST',
      body: JSON.stringify({ action: 'stop', pan: 0, tilt: 0, zoom: 0 }),
    })
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <p className="text-sm font-medium text-muted-foreground">PTZ Controls</p>
      <div className="grid grid-cols-3 gap-1">
        <div />
        <Button variant="outline" size="icon" onMouseDown={() => sendPTZ(0, 0.5, 0)} onMouseUp={stopPTZ}>
          <ArrowUp className="h-4 w-4" />
        </Button>
        <div />
        <Button variant="outline" size="icon" onMouseDown={() => sendPTZ(-0.5, 0, 0)} onMouseUp={stopPTZ}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <Button variant="outline" size="icon" onClick={stopPTZ}>
          <Square className="h-3 w-3" />
        </Button>
        <Button variant="outline" size="icon" onMouseDown={() => sendPTZ(0.5, 0, 0)} onMouseUp={stopPTZ}>
          <ArrowRight className="h-4 w-4" />
        </Button>
        <div />
        <Button variant="outline" size="icon" onMouseDown={() => sendPTZ(0, -0.5, 0)} onMouseUp={stopPTZ}>
          <ArrowDown className="h-4 w-4" />
        </Button>
        <div />
      </div>
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onMouseDown={() => sendPTZ(0, 0, 0.5)} onMouseUp={stopPTZ}>
          <ZoomIn className="mr-1 h-4 w-4" /> Zoom In
        </Button>
        <Button variant="outline" size="sm" onMouseDown={() => sendPTZ(0, 0, -0.5)} onMouseUp={stopPTZ}>
          <ZoomOut className="mr-1 h-4 w-4" /> Zoom Out
        </Button>
      </div>
    </div>
  )
}
