'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { User, getUser, isAuthenticated, logout } from '@/lib/auth'

export function useAuth(requireAuth = true) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const authenticated = isAuthenticated()
    if (requireAuth && !authenticated) {
      router.push('/login')
      return
    }
    setUser(getUser())
    setLoading(false)
  }, [requireAuth, router])

  return { user, loading, logout }
}
