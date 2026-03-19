'use client'

import { useRef, useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'

interface Point {
  x: number
  y: number
}

interface ZoneEditorProps {
  initialPoints?: Point[]
  onSave: (points: Point[]) => void
  width?: number
  height?: number
}

export function ZoneEditor({ initialPoints = [], onSave, width = 640, height = 360 }: ZoneEditorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [points, setPoints] = useState<Point[]>(initialPoints)
  const [isDrawing, setIsDrawing] = useState(true)

  const draw = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.clearRect(0, 0, width, height)

    if (points.length === 0) return

    // Draw filled polygon
    ctx.beginPath()
    ctx.moveTo(points[0].x * width, points[0].y * height)
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x * width, points[i].y * height)
    }
    ctx.closePath()
    ctx.fillStyle = 'rgba(59, 130, 246, 0.2)'
    ctx.fill()
    ctx.strokeStyle = '#3b82f6'
    ctx.lineWidth = 2
    ctx.stroke()

    // Draw points
    for (const point of points) {
      ctx.beginPath()
      ctx.arc(point.x * width, point.y * height, 5, 0, Math.PI * 2)
      ctx.fillStyle = '#3b82f6'
      ctx.fill()
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 1
      ctx.stroke()
    }
  }, [points, width, height])

  useEffect(() => {
    draw()
  }, [draw])

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return

    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height

    setPoints([...points, { x: parseFloat(x.toFixed(4)), y: parseFloat(y.toFixed(4)) }])
  }

  return (
    <div className="space-y-3">
      <div className="relative overflow-hidden rounded-lg border bg-black">
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          onClick={handleCanvasClick}
          className="cursor-crosshair"
          style={{ width: '100%', height: 'auto' }}
        />
      </div>
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            setPoints([])
            setIsDrawing(true)
          }}
        >
          Clear
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setPoints(points.slice(0, -1))}
          disabled={points.length === 0}
        >
          Undo
        </Button>
        <Button
          size="sm"
          onClick={() => {
            setIsDrawing(false)
            onSave(points)
          }}
          disabled={points.length < 3}
        >
          Save Zone ({points.length} points)
        </Button>
      </div>
    </div>
  )
}
