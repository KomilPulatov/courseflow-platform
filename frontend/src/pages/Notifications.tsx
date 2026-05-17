import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMyNotifications, type Notification } from '../api/notifications'

export default function Notifications() {
  const [items, setItems] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getMyNotifications()
      .then(setItems)
      .catch(() => setError('Could not load notifications.'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-8">
        <Link to="/student" className="text-sm text-gray-400 hover:text-gray-600 mb-6 block">
          ← Dashboard
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Notifications</h1>

        {loading && <p className="text-gray-400 text-sm">Loading…</p>}
        {error && <p className="text-red-500 text-sm">{error}</p>}

        {!loading && !error && items.length === 0 && (
          <div className="bg-white border border-gray-200 rounded-2xl p-6 text-center text-gray-400 text-sm">
            No notifications yet.
          </div>
        )}

        <div className="space-y-3">
          {items.map((n) => (
            <div
              key={n.id}
              className={`bg-white border rounded-xl p-4 ${
                n.status === 'unread' ? 'border-blue-200' : 'border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm text-gray-800">{n.message}</p>
                {n.status === 'unread' && (
                  <span className="w-2 h-2 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" />
                )}
              </div>
              <p className="text-xs text-gray-400 mt-1">
                {new Date(n.created_at).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
