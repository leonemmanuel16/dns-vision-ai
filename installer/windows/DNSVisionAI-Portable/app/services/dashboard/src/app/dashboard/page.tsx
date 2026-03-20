'use client'

import { useState, useEffect } from 'react'
import { apiFetch } from '@/lib/api'
import { StatsCard } from '@/components/StatsCard'
import { EventTimeline } from '@/components/EventTimeline'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Camera, Bell, Wifi, Activity } from 'lucide-react'

interface DashboardStats {
  total_cameras: number
  online_cameras: number
  total_events_today: number
  total_events_week: number
  events_by_type: Record<string, number>
  recent_events: any[]
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchStats() {
      try {
        const data = await apiFetch<DashboardStats>('/api/dashboard/stats')
        setStats(data)
      } catch (e) {
        console.error('Failed to load dashboard stats:', e)
      } finally {
        setLoading(false)
      }
    }
    fetchStats()
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return <div className="animate-pulse text-muted-foreground">Loading dashboard...</div>
  }

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">Dashboard</h2>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Cameras"
          value={stats?.total_cameras || 0}
          icon={Camera}
        />
        <StatsCard
          title="Online"
          value={stats?.online_cameras || 0}
          icon={Wifi}
          description={`of ${stats?.total_cameras || 0} cameras`}
        />
        <StatsCard
          title="Events Today"
          value={stats?.total_events_today || 0}
          icon={Bell}
        />
        <StatsCard
          title="Events This Week"
          value={stats?.total_events_week || 0}
          icon={Activity}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Events by Type</CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.events_by_type && Object.keys(stats.events_by_type).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(stats.events_by_type).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-sm capitalize">{type}</span>
                    <div className="flex items-center gap-2">
                      <div className="h-2 rounded-full bg-primary" style={{ width: `${Math.min(count * 2, 200)}px` }} />
                      <span className="text-sm font-medium">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No events recorded yet</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Events</CardTitle>
          </CardHeader>
          <CardContent>
            <EventTimeline events={stats?.recent_events || []} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
