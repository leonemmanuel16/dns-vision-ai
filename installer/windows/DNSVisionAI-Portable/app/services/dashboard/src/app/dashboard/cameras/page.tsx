'use client'

import { useState } from 'react'
import { useCameras } from '@/hooks/useCameras'
import { CameraGrid } from '@/components/CameraGrid'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { apiFetch } from '@/lib/api'
import { Plus, RefreshCw } from 'lucide-react'

export default function CamerasPage() {
  const { cameras, loading, refresh } = useCameras()
  const [showAdd, setShowAdd] = useState(false)
  const [name, setName] = useState('')
  const [ip, setIp] = useState('')
  const [port, setPort] = useState('80')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [location, setLocation] = useState('')
  const [adding, setAdding] = useState(false)

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    setAdding(true)
    try {
      await apiFetch('/api/cameras', {
        method: 'POST',
        body: JSON.stringify({
          name,
          ip_address: ip,
          onvif_port: parseInt(port),
          username: username || undefined,
          password: password || undefined,
          location: location || undefined,
        }),
      })
      setShowAdd(false)
      setName('')
      setIp('')
      setPort('80')
      setUsername('')
      setPassword('')
      setLocation('')
      refresh()
    } catch (e) {
      console.error('Failed to add camera:', e)
    } finally {
      setAdding(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold">Cameras</h2>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={refresh}>
            <RefreshCw className="mr-2 h-4 w-4" /> Refresh
          </Button>
          <Button size="sm" onClick={() => setShowAdd(!showAdd)}>
            <Plus className="mr-2 h-4 w-4" /> Add Camera
          </Button>
        </div>
      </div>

      {showAdd && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Add Camera</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAdd} className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              <Input placeholder="Camera Name" value={name} onChange={(e) => setName(e.target.value)} required />
              <Input placeholder="IP Address" value={ip} onChange={(e) => setIp(e.target.value)} required />
              <Input placeholder="ONVIF Port" type="number" value={port} onChange={(e) => setPort(e.target.value)} />
              <Input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
              <Input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
              <Input placeholder="Location" value={location} onChange={(e) => setLocation(e.target.value)} />
              <div className="flex gap-2 md:col-span-2 lg:col-span-3">
                <Button type="submit" disabled={adding}>{adding ? 'Adding...' : 'Add Camera'}</Button>
                <Button type="button" variant="outline" onClick={() => setShowAdd(false)}>Cancel</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="animate-pulse text-muted-foreground">Loading cameras...</div>
      ) : cameras.length === 0 ? (
        <div className="flex h-40 items-center justify-center text-muted-foreground">
          No cameras configured. Add a camera to get started.
        </div>
      ) : (
        <CameraGrid cameras={cameras} columns={3} />
      )}
    </div>
  )
}
