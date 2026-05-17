import { useEffect, useRef, useState } from 'react'

const WS_BASE = (import.meta.env.VITE_API_BASE ?? 'http://localhost:8000')
  .replace(/^http/, 'ws')

export interface RegistrationEvent {
  type: string
  enrollment_id?: number
  section_id?: number
  position?: number
  message?: string
}

export function useRegistrationWS(userId: string) {
  const [lastEvent, setLastEvent] = useState<RegistrationEvent | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!userId) return
    let cancelled = false

    function connect() {
      if (cancelled) return
      const ws = new WebSocket(`${WS_BASE}/ws/registrations/${userId}`)
      wsRef.current = ws

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type !== 'connected') setLastEvent(data)
        } catch {}
      }

      ws.onclose = () => {
        if (!cancelled) retryRef.current = setTimeout(connect, 3000)
      }
    }

    connect()

    return () => {
      cancelled = true
      if (retryRef.current) clearTimeout(retryRef.current)
      wsRef.current?.close()
    }
  }, [userId])

  return lastEvent
}
