import { useEffect, useRef, useState } from 'react'

function websocketBaseUrl() {
  const explicitBase = import.meta.env.VITE_API_BASE
  if (explicitBase) return explicitBase.replace(/^http/, 'ws')
  return `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
}

export interface SectionAvailabilityUpdate {
  section_id: number
  remaining_seats: number
  enrolled_count: number
  waitlist_count: number
  capacity: number
}

export function useSectionWS(sectionId: number) {
  const [availability, setAvailability] = useState<SectionAvailabilityUpdate | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    let cancelled = false

    function connect() {
      if (cancelled) return
      const ws = new WebSocket(`${websocketBaseUrl()}/ws/sections/${sectionId}`)
      wsRef.current = ws

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type !== 'connected') setAvailability(data)
        } catch {
          console.warn('Ignored invalid section websocket payload.')
        }
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
  }, [sectionId])

  return availability
}
