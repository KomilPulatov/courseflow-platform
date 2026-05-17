import client from './client'

export interface Notification {
  id: number
  event_type: string
  message: string
  status: 'unread' | 'read' | 'archived'
  created_at: string
}

export async function getMyNotifications(): Promise<Notification[]> {
  const res = await client.get('/api/v1/notifications/me')
  return res.data
}
