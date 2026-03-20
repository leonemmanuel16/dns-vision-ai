'use client'

import { useState, useEffect } from 'react'
import { apiFetch } from '@/lib/api'
import { useCameras } from '@/hooks/useCameras'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Plus, Trash2 } from 'lucide-react'

interface AlertRule {
  id: string
  name: string
  camera_id: string | null
  zone_id: string | null
  event_types: string[]
  channel: string
  target: string
  cooldown_seconds: number
  is_enabled: boolean
  last_triggered_at: string | null
  created_at: string
}

export default function AlertsPage() {
  const { cameras } = useCameras()
  const [rules, setRules] = useState<AlertRule[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [cameraId, setCameraId] = useState('')
  const [channel, setChannel] = useState('webhook')
  const [target, setTarget] = useState('')
  const [eventTypes, setEventTypes] = useState<string[]>(['person'])
  const [cooldown, setCooldown] = useState('60')

  useEffect(() => {
    fetchRules()
  }, [])

  async function fetchRules() {
    try {
      const data = await apiFetch<{ rules: AlertRule[]; total: number }>('/api/alerts')
      setRules(data.rules)
    } catch (e) {
      console.error('Failed to load alert rules:', e)
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    try {
      await apiFetch('/api/alerts', {
        method: 'POST',
        body: JSON.stringify({
          name,
          camera_id: cameraId || null,
          event_types: eventTypes,
          channel,
          target,
          cooldown_seconds: parseInt(cooldown),
        }),
      })
      setShowCreate(false)
      setName('')
      setTarget('')
      fetchRules()
    } catch (e) {
      console.error('Failed to create alert rule:', e)
    }
  }

  async function handleDelete(ruleId: string) {
    if (!confirm('Delete this alert rule?')) return
    try {
      await apiFetch(`/api/alerts/${ruleId}`, { method: 'DELETE' })
      fetchRules()
    } catch (e) {
      console.error('Failed to delete rule:', e)
    }
  }

  async function handleToggle(rule: AlertRule) {
    try {
      await apiFetch(`/api/alerts/${rule.id}`, {
        method: 'PUT',
        body: JSON.stringify({ is_enabled: !rule.is_enabled }),
      })
      fetchRules()
    } catch (e) {
      console.error('Failed to toggle rule:', e)
    }
  }

  const toggleEventType = (type: string) => {
    setEventTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold">Alert Rules</h2>
        <Button size="sm" onClick={() => setShowCreate(!showCreate)}>
          <Plus className="mr-2 h-4 w-4" /> Create Rule
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Create Alert Rule</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <Input placeholder="Rule Name" value={name} onChange={(e) => setName(e.target.value)} required />
                <select className="rounded-md border bg-background px-3 py-2 text-sm" value={cameraId} onChange={(e) => setCameraId(e.target.value)}>
                  <option value="">All Cameras</option>
                  {cameras.map((cam) => (
                    <option key={cam.id} value={cam.id}>{cam.name}</option>
                  ))}
                </select>
                <select className="rounded-md border bg-background px-3 py-2 text-sm" value={channel} onChange={(e) => setChannel(e.target.value)}>
                  <option value="webhook">Webhook</option>
                  <option value="whatsapp">WhatsApp</option>
                  <option value="email">Email</option>
                </select>
                <Input placeholder={channel === 'webhook' ? 'Webhook URL' : channel === 'whatsapp' ? 'Phone Number' : 'Email Address'} value={target} onChange={(e) => setTarget(e.target.value)} required />
                <Input placeholder="Cooldown (seconds)" type="number" value={cooldown} onChange={(e) => setCooldown(e.target.value)} />
              </div>
              <div>
                <p className="mb-2 text-sm font-medium">Event Types:</p>
                <div className="flex flex-wrap gap-2">
                  {['person', 'vehicle', 'animal', 'zone_crossing'].map((type) => (
                    <Badge
                      key={type}
                      variant={eventTypes.includes(type) ? 'default' : 'outline'}
                      className="cursor-pointer"
                      onClick={() => toggleEventType(type)}
                    >
                      {type}
                    </Badge>
                  ))}
                </div>
              </div>
              <div className="flex gap-2">
                <Button type="submit">Create Rule</Button>
                <Button type="button" variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="animate-pulse text-muted-foreground">Loading rules...</div>
      ) : rules.length === 0 ? (
        <div className="flex h-40 items-center justify-center text-muted-foreground">
          No alert rules configured.
        </div>
      ) : (
        <div className="space-y-3">
          {rules.map((rule) => {
            const cam = cameras.find((c) => c.id === rule.camera_id)
            return (
              <Card key={rule.id}>
                <CardContent className="flex items-center justify-between p-4">
                  <div>
                    <p className="font-medium">{rule.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {cam?.name || 'All cameras'} | {rule.channel} | Cooldown: {rule.cooldown_seconds}s
                    </p>
                    <div className="mt-2 flex gap-1">
                      {rule.event_types.map((t) => (
                        <Badge key={t} variant="secondary">{t}</Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant={rule.is_enabled ? 'outline' : 'default'}
                      size="sm"
                      onClick={() => handleToggle(rule)}
                    >
                      {rule.is_enabled ? 'Disable' : 'Enable'}
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => handleDelete(rule.id)}>
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
