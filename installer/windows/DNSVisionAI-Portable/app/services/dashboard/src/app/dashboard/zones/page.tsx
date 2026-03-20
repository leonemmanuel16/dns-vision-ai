'use client'

import { useState, useEffect } from 'react'
import { apiFetch } from '@/lib/api'
import { useCameras } from '@/hooks/useCameras'
import { ZoneEditor } from '@/components/ZoneEditor'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Plus, Trash2 } from 'lucide-react'

interface Zone {
  id: string
  camera_id: string
  name: string
  zone_type: string
  points: { x: number; y: number }[]
  direction: string | null
  detect_classes: string[]
  is_enabled: boolean
  created_at: string
}

export default function ZonesPage() {
  const { cameras } = useCameras()
  const [zones, setZones] = useState<Zone[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [selectedCamera, setSelectedCamera] = useState('')
  const [zoneName, setZoneName] = useState('')
  const [zoneType, setZoneType] = useState('roi')

  useEffect(() => {
    fetchZones()
  }, [])

  async function fetchZones() {
    try {
      const data = await apiFetch<{ zones: Zone[]; total: number }>('/api/zones')
      setZones(data.zones)
    } catch (e) {
      console.error('Failed to load zones:', e)
    } finally {
      setLoading(false)
    }
  }

  async function handleSaveZone(points: { x: number; y: number }[]) {
    if (!selectedCamera || !zoneName) return
    try {
      await apiFetch('/api/zones', {
        method: 'POST',
        body: JSON.stringify({
          camera_id: selectedCamera,
          name: zoneName,
          zone_type: zoneType,
          points,
        }),
      })
      setShowCreate(false)
      setZoneName('')
      fetchZones()
    } catch (e) {
      console.error('Failed to create zone:', e)
    }
  }

  async function handleDelete(zoneId: string) {
    if (!confirm('Delete this zone?')) return
    try {
      await apiFetch(`/api/zones/${zoneId}`, { method: 'DELETE' })
      fetchZones()
    } catch (e) {
      console.error('Failed to delete zone:', e)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold">Zones</h2>
        <Button size="sm" onClick={() => setShowCreate(!showCreate)}>
          <Plus className="mr-2 h-4 w-4" /> Create Zone
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Create Zone</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <select
                className="rounded-md border bg-background px-3 py-2 text-sm"
                value={selectedCamera}
                onChange={(e) => setSelectedCamera(e.target.value)}
              >
                <option value="">Select Camera</option>
                {cameras.map((cam) => (
                  <option key={cam.id} value={cam.id}>{cam.name}</option>
                ))}
              </select>
              <Input
                placeholder="Zone Name"
                value={zoneName}
                onChange={(e) => setZoneName(e.target.value)}
              />
              <select
                className="rounded-md border bg-background px-3 py-2 text-sm"
                value={zoneType}
                onChange={(e) => setZoneType(e.target.value)}
              >
                <option value="roi">Region of Interest</option>
                <option value="tripwire">Tripwire</option>
                <option value="perimeter">Perimeter</option>
              </select>
            </div>
            {selectedCamera && zoneName && (
              <ZoneEditor onSave={handleSaveZone} />
            )}
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="animate-pulse text-muted-foreground">Loading zones...</div>
      ) : zones.length === 0 ? (
        <div className="flex h-40 items-center justify-center text-muted-foreground">
          No zones configured. Create a zone to define detection areas.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {zones.map((zone) => {
            const cam = cameras.find((c) => c.id === zone.camera_id)
            return (
              <Card key={zone.id}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium">{zone.name}</p>
                      <p className="text-xs text-muted-foreground">{cam?.name || 'Unknown camera'}</p>
                      <div className="mt-2 flex gap-1">
                        <Badge variant="secondary">{zone.zone_type}</Badge>
                        <Badge variant={zone.is_enabled ? 'success' : 'outline'}>
                          {zone.is_enabled ? 'Active' : 'Disabled'}
                        </Badge>
                      </div>
                      <p className="mt-2 text-xs text-muted-foreground">
                        {zone.points.length} points | Classes: {zone.detect_classes?.join(', ') || 'all'}
                      </p>
                    </div>
                    <Button variant="ghost" size="icon" onClick={() => handleDelete(zone.id)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
